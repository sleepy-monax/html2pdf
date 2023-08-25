import base64
import logging

from typing import Optional
from dataclasses import dataclass
from pycdp.asyncio import CDPSession
from pycdp import cdp
from . import monkeys

_logger = logging.getLogger(__name__)

@dataclass
class Options:
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

async def runOnSession(
        session: CDPSession,
        object: str,
        options: Optional[Options] = None) -> bytes:

    if options is None:
        options = Options()

    await session.execute(cdp.page.set_lifecycle_events_enabled(enabled=True))

    _logger.info('Waiting for network idle...')
    async for ev in session.listen(cdp.page.LifecycleEvent):
        if ev.name == 'networkIdle':
            break

    with session.safe_wait_for(cdp.page.DomContentEventFired) as navigation:
        await session.execute(cdp.page.navigate(object))
        await navigation

    _logger.info('Page loaded, printing...')

    pdf_base64 = await session.execute(
        cdp.page.print_to_pdf(
            **options.__dict__, display_header_footer=options.footer_template is not None or options.header_template is not None)
    )

    _logger.info('Page printed')

    return base64.b64decode(pdf_base64[0])

async def runOnRemote(
        remote: str,
        object: str,
        options: Optional[Options] = None) -> bytes:

    _logger.info('Connecting to Chrome...')
    conn = await monkeys.connect_cdp(remote)

    _logger.info(f'Printing using {options}...')
    target_id = await conn.execute(cdp.target.create_target('about:blank'))
    session = await conn.connect_session(target_id)
    await session.execute(cdp.page.enable())
    pdf_data = await runOnSession(session, object, options)
    await session.execute(cdp.page.close())
    await conn.close()

    return pdf_data
