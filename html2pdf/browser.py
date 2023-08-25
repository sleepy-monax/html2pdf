import logging
import shutil
import os

from typing import Optional
from pycdp.browser import ChromeLauncher
from asyncio import get_running_loop
from random import randint
from . import consts

_logger = logging.getLogger(__name__)

class ContextManager:
    url : str
    _chrome : ChromeLauncher

    def __init__(self, url : str, chrome: ChromeLauncher):
        self.url = url
        self._chrome = chrome

    async def __aenter__(self):
        _logger.info('Starting Chrome...')
        await get_running_loop().run_in_executor(None, self._chrome.launch)
        return self

    async def __aexit__(self, type, value, traceback):
        _logger.info('Stopping Chrome...')
        await get_running_loop().run_in_executor(None, self._chrome.kill)

def find() -> Optional[str]:
    """
    Search for a Chromium executable in the system.
    Either by walking through the PATH environment variable or the
    ODOO_HTML2PDF_BROWSER environment variable.
    """
    if consts.BROWSER_ENV_VAR in os.environ:
        return os.environ[consts.BROWSER_ENV_VAR]

    for executable in consts.BROWSER_EXECUTABLE:
        target = shutil.which(executable)
        if target is not None:
            return target

    return None

def ensure() -> str:
    maybePath = find()
    if maybePath is None:
        raise RuntimeError(
            "Could not find Chromium executable. Please install Chromium or set the O_HTML2PDF_BROWSER environment variable."
        )
    return maybePath

def open(chromePath : str, port = randint(*consts.BROWSER_PORT_RANGE)) -> ContextManager:
    url = f'http://localhost:{port}'
    _logger.info(f'Using browser at {chromePath}...')

    return ContextManager(url, ChromeLauncher(
        binary=chromePath,
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
            f'--remote-debugging-port={port}',
        ]
    ))
