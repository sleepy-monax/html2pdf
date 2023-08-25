from pycdp.asyncio import  CDPConnection, loop, ClientSession
from aiohttp import  ClientConnectorError, ClientResponseError, ClientConnectionError, ServerDisconnectedError
from asyncio import TimeoutError
from pycdp.utils import retry_on

class MonkeyPatchCDPConnection(CDPConnection):
    """
    Patch to the pycdp's CDPConnection to increase the the maximum
    message size to 4GB. This is necessary because the default
    maximum message size of 4MB is too small for large PDFs.
    """

    @retry_on(
        ClientConnectorError, TimeoutError,
        retries=10, delay=3.0, delay_growth=1.3, log_errors=True, loop=loop
    )
    async def connect(self):
        if self._ws is not None: raise RuntimeError('already connected')
        if self._wsurl is None:
            if self._debugging_url.startswith('http://'):
                async with self._http_client.get(f'{self._debugging_url}/json/version') as resp:
                    if resp.status != 200:
                        raise ClientResponseError(
                            resp.request_info,
                            resp.history,
                            status=resp.status,
                            message=resp.reason,
                            headers=resp.headers
                        )
                    self._wsurl = (await resp.json())['webSocketDebuggerUrl']
            elif self._debugging_url.startswith('ws://'):
                self._wsurl = self._debugging_url
            else:
                raise ValueError('bad debugging URL scheme')
        self._ws = await self._http_client.ws_connect(self._wsurl, compress=15, autoping=True, autoclose=True, max_msg_size=4*1024*1024*1024).__aenter__()


@retry_on(ClientConnectionError, ServerDisconnectedError, retries=10, delay=3.0, delay_growth=1.3, log_errors=True, loop=loop)
async def connect_cdp(url: str) -> CDPConnection:
    '''
    Connect to the browser specified by debugging ``url``.

    This connection is not automatically closed! You can either use the connection
    object as a context manager (``async with conn:``) or else call ``await
    conn.aclose()`` on it when you are done with it.
    '''
    http = ClientSession()

    cdp_conn = MonkeyPatchCDPConnection(url, http)
    try:
        await cdp_conn.connect()
        cdp_conn.start()
    except:
        await http.close()
        raise
    return cdp_conn
