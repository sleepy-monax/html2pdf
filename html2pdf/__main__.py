from . import VERSION

from dataclasses import dataclass
from pycdp import cdp
from pycdp.asyncio import connect_cdp, CDPSession
from pycdp.browser import ChromeLauncher
from typing import Optional

import argparse
import asyncio
import base64
import os
import random


@dataclass
class Html2PdfOptions:
    landscape: Optional[bool] = None
    print_background: Optional[bool] = None
    scale: Optional[float] = None
    paper_width: Optional[float] = None
    paper_height: Optional[float] = None
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    margin_left: Optional[float] = None
    margin_right: Optional[float] = None
    page_ranges: Optional[str] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    prefer_css_page_size: Optional[bool] = None


async def html2pdf(
        session: CDPSession,
        object: str,
        options: Optional[Html2PdfOptions] = None) -> bytes:

    if options is None:
        options = Html2PdfOptions()

    await session.execute(cdp.page.set_lifecycle_events_enabled(enabled=True))

    print('Waiting for network idle...')
    async for ev in session.listen(cdp.page.LifecycleEvent):
        if ev.name == 'networkIdle':
            break

    with session.safe_wait_for(cdp.page.DomContentEventFired) as navigation:
        await session.execute(cdp.page.navigate(object))
        await navigation

    pdf_base64 = await session.execute(
        cdp.page.print_to_pdf(
            **options.__dict__, display_header_footer=options.footer_template is not None or options.header_template is not None)
    )

    return base64.b64decode(pdf_base64[0])


async def html2pdf_remote(
        remote: str,
        object: str,
        options: Optional[Html2PdfOptions] = None) -> bytes:
    print('Connecting to Chrome...')
    conn = await connect_cdp(remote)

    print(f'Printing using {options}...')
    target_id = await conn.execute(cdp.target.create_target('about:blank'))
    session = await conn.connect_session(target_id)
    await session.execute(cdp.page.enable())
    pdf_data = await html2pdf(session, object, options)
    await session.execute(cdp.page.close())
    await conn.close()

    return pdf_data


def find_chrome() -> str:
    KNOWN_PATHS = [
        # linux path
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/bin/chrome',

        # macos path
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        # windows path
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ]

    for path in KNOWN_PATHS:
        if os.path.exists(path):
            print(f'Using Chrome at {path}')
            return path

    raise RuntimeError('Chrome not found')


def mmtoinch(mm: Optional[float]) -> Optional[float]:
    if mm is None:
        return None
    return mm / 25.4


async def main():
    parser = argparse.ArgumentParser(
        prog='html2pdf', description='Convert HTML to PDF using Chrome Headless')

    parser.add_argument('object', help='HTML files or URLs')
    parser.add_argument('output', help='Output file')

    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {VERSION}')
    parser.add_argument('--remote', help='Remote debugging URL')
    parser.add_argument('--chrome', help='Chrome binary path')

    output_group = parser.add_argument_group('Output options')
    output_group.add_argument('--landscape', action='store_true')
    output_group.add_argument('--print-background', action='store_true')
    output_group.add_argument('--scale', type=float)
    output_group.add_argument('--paper-width', type=float)
    output_group.add_argument('--paper-height', type=float)

    output_group.add_argument('--margin-top', type=float)
    output_group.add_argument('--margin-bottom', type=float)
    output_group.add_argument('--margin-left', type=float)
    output_group.add_argument('--margin-right', type=float)
    output_group.add_argument('--margin-all', type=float)
    output_group.add_argument('--margin-horiz', type=float)
    output_group.add_argument('--margin-vert', type=float)

    output_group.add_argument('--page-ranges')
    output_group.add_argument('--header-template')
    output_group.add_argument('--footer-template')
    output_group.add_argument('--prefer-css-page-size', action='store_true')

    args = parser.parse_args()

    randomPort = random.randint(9222, 9322)

    options = Html2PdfOptions(
        landscape=args.landscape,
        print_background=args.print_background,
        scale=args.scale,
        paper_width=mmtoinch(args.paper_width),
        paper_height=mmtoinch(args.paper_height),
        margin_top=mmtoinch(
            args.margin_top or args.margin_vert or args.margin_all),
        margin_bottom=mmtoinch(
            args.margin_bottom or args.margin_vert or args.margin_all),
        margin_left=mmtoinch(
            args.margin_left or args.margin_horiz or args.margin_all),
        margin_right=mmtoinch(
            args.margin_right or args.margin_horiz or args.margin_all),
        page_ranges=args.page_ranges,
        header_template=args.header_template,
        footer_template=args.footer_template,
        prefer_css_page_size=args.prefer_css_page_size,
    )

    chrome = ChromeLauncher(
        binary=args.chrome or find_chrome(),
        headless=True,
        args=[
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-gpu',
            '--disable-sync',
            '--disable-translate',
            '--headless',
            '--hide-scrollbars',
            '--incognito',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            f'--remote-debugging-port={randomPort}',
        ]
    )

    pdf_data = None

    if args.remote:
        pdf_data = await html2pdf_remote(args.remote, args.object, options)
    else:
        await asyncio.get_running_loop().run_in_executor(None, chrome.launch)
        try:
            pdf_data = await html2pdf_remote(f'http://localhost:{randomPort}', args.object, options)
        finally:
            await asyncio.get_running_loop().run_in_executor(None, chrome.kill)

    if pdf_data is None:
        raise RuntimeError('Failed to generate PDF')

    print('Writing...')
    with open(args.output, 'wb') as f:
        f.write(pdf_data)

asyncio.run(main())
