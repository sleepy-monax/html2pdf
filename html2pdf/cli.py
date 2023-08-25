import asyncio
import sys
import logging

from . import browser, pdfgen, utils, consts, papers
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace

ROOT = ArgumentParser(
        prog=sys.argv[0],
        description='Convert HTML to PDF using Chrome Headless',
        formatter_class=RawTextHelpFormatter)

ROOT.add_argument('--version', action='version',
                    version=f'%(prog)s {consts.VERSION}')
ROOT.add_argument('--verbose', action='store_true')

subparser = ROOT.add_subparsers(dest='command', required=True, help='command to run')

# --- Render Subcommand ---------------------------------------------- #

render_subcommand = subparser.add_parser('render', help='render HTML to PDF', formatter_class=RawTextHelpFormatter)
render_subcommand.add_argument('--output', help='output file default: %(default)s', default='stdout')
render_subcommand.add_argument('input', help='local file or URL to convert')

browser_group = render_subcommand.add_argument_group('browser options')
browser_group.add_argument('--browser', help='browser binary path or URL')

output_group = render_subcommand.add_argument_group('output options')
output_group.add_argument('--page-ranges')
output_group.add_argument('--landscape', action='store_true')
output_group.add_argument('--scale', type=float)
output_group.add_argument('--print-background', action='store_true')

output_group.add_argument('--paper', choices=papers.NAMES, default='A4')
output_group.add_argument('--paper-width', type=float, help='in mm')
output_group.add_argument('--paper-height', type=float, help='in mm')

output_group.add_argument('--margin-top', type=float, help='in mm')
output_group.add_argument('--margin-bottom', type=float, help='in mm')
output_group.add_argument('--margin-left', type=float, help='in mm')
output_group.add_argument('--margin-right', type=float, help='in mm')
output_group.add_argument('--margin-all', type=float, help='in mm')
output_group.add_argument('--margin-horiz', type=float, help='in mm')
output_group.add_argument('--margin-vert', type=float, help='in mm')

output_group.add_argument('--header-template')
output_group.add_argument('--footer-template')

output_group.add_argument('--prefer-css-page-size', action='store_true')

render_subcommand.epilog = f"""
examples:
    {sys.argv[0]} render https://www.google.com/ google.pdf
    {sys.argv[0]} render --browser http://localhost:9222 https://www.google.com/ google.pdf
    {sys.argv[0]} render --browser /usr/bin/chromium https://www.google.com/ google.pdf

browser lookup order:
    When determining the browser to use, the following order is used:
    1. --browser
    3. {consts.BROWSER_ENV_VAR}
    4. looking for {', '.join(consts.BROWSER_EXECUTABLE)} in the PATH

environment variables:
    {consts.BROWSER_ENV_VAR} - Path to the browser executable

paper sizes:
{consts.NEWLINE.join(f'    {p.key} - {p.description}' for p in papers.STOCKS)}
"""


def parseOption(args : Namespace) -> pdfgen.Options:
    return pdfgen.Options(
        landscape=args.landscape,
        print_background=args.print_background,
        scale=args.scale,
        paper_width=utils.mmtoinch(args.paper_width),
        paper_height=utils.mmtoinch(args.paper_height),
        margin_top=utils.mmtoinch(
            args.margin_top or args.margin_vert or args.margin_all),
        margin_bottom=utils.mmtoinch(
            args.margin_bottom or args.margin_vert or args.margin_all),
        margin_left=utils.mmtoinch(
            args.margin_left or args.margin_horiz or args.margin_all),
        margin_right=utils.mmtoinch(
            args.margin_right or args.margin_horiz or args.margin_all),
        page_ranges=args.page_ranges,
        header_template=args.header_template,
        footer_template=args.footer_template,
        prefer_css_page_size=args.prefer_css_page_size,
    )

async def renderSubCommand(args : Namespace) -> int:
    pdfData = None
    options = parseOption(args)

    browserUrl = args.browser or browser.ensure()
    if browserUrl.startswith('http://') or browserUrl.startswith('https://'):
        pdfData = await pdfgen.runOnRemote(browserUrl, args.input, options)
    else:
        async with browser.open(browserUrl or browser.ensure()) as c:
            pdfData = await pdfgen.runOnRemote(c.url, args.input, options)

    assert pdfData is not None

    if args.output == 'stdout':
        sys.stdout.buffer.write(pdfData)
    else:
        with open(args.output, 'wb') as f:
            f.write(pdfData)

    return 0

render_subcommand.set_defaults(func=renderSubCommand)

# --- Serve Subcommand ----------------------------------------------- #

serve_subcommand = subparser.add_parser('serve', help='start as a server', formatter_class=RawTextHelpFormatter)
serve_subcommand.add_argument('--port', type=int, default=9222, help='port to listen on')
serve_subcommand.add_argument('--browser', help='browser binary path or URL')

async def serveSubCommand(args : Namespace) -> int:
    async with browser.open(args.browser or browser.ensure()) as c:
        logging.info(f'Listening on {c.url}')
        while True:
            logging.info('Heartbeat')
            await asyncio.sleep(60)

serve_subcommand.set_defaults(func=serveSubCommand)

# --- Main ----------------------------------------------------------- #

async def mainAsync(argv : list[str]) -> int:
    args = ROOT.parse_args(argv[1:])
    if args.verbose:
        BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _NOTHING, DEFAULT = range(10)
        RESET_SEQ = "\033[0m"
        COLOR_SEQ = "\033[1;%dm"
        BOLD_SEQ = "\033[1m"
        COLOR_PATTERN = "%s%s%%s%s" % (COLOR_SEQ, COLOR_SEQ, RESET_SEQ)
        LEVEL_COLOR_MAPPING = {
            logging.DEBUG: (BLUE, DEFAULT),
            logging.INFO: (GREEN, DEFAULT),
            logging.WARNING: (YELLOW, DEFAULT),
            logging.ERROR: (RED, DEFAULT),
            logging.CRITICAL: (WHITE, RED),
        }

        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                fg_color, bg_color = LEVEL_COLOR_MAPPING.get(record.levelno, (GREEN, DEFAULT))
                record.levelname = COLOR_PATTERN % (30 + fg_color, 40 + bg_color, record.levelname)
                return super().format(record)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        logging.basicConfig( level=logging.DEBUG, handlers=[handler])
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
    return await args.func(args)

def main(argv : list[str] = sys.argv) -> int:
    return asyncio.run(mainAsync(argv))
