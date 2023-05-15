import json
from websockets import connect, WebSocketClientProtocol, ConnectionClosed, InvalidStatusCode
from .channel import *
from .types import *
from .utils import *
import logging

TEST_WS_PUBLIC_URL = "wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999"
TEST_WS_PRIVATE_URL = "wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999"

WS_PUBLIC_URL = "wss://wsaws.okx.com:8443/ws/v5/public"
WS_PRIVATE_URL = "wss://wsaws.okx.com:8443/ws/v5/private"

TEST_WS_BIZ_URL = "wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999"
WS_BIZ_URL = "wss://wsaws.okx.com:8443/ws/v5/business"


def get_local_timestamp():
    return int(time.time())


class PublicSubscription:
    """PublicSubscription is an async generator of websocket stream on specific channels"""

    def __init__(self, uri, channels: Sequence[Channel], **ws_kwargs):
        self.uri = uri
        self.channels = channels
        self.ws: Optional[WebSocketClientProtocol] = None
        self.ws_kwargs = ws_kwargs
        self.ping_interval = 25
        self.logger = logging.getLogger(",".join([c["channel"] for c in channels]))
        self.logger.setLevel(logging.DEBUG)

    SUBSCRIPTION_SEMAPHORE = RateLimiter(240, 3600)

    async def subscribe(self):
        try:
            self.ws = await connect(self.uri, **self.ws_kwargs)
            sub_params = {"op": "subscribe", "args": self.channels}
            sub_str = json.dumps(sub_params)
            async with self.SUBSCRIPTION_SEMAPHORE:
                await self.ws.send(sub_str)
            self.logger.debug(f"send: {sub_str}")
        except Exception as exc:
            self.logger.error(f"Websocket subscribe error", exc_info=exc)

    async def unsubscribe(self):
        sub_params = {"op": "unsubscribe", "args": self.channels}
        sub_str = json.dumps(sub_params)
        await self.ws.send(sub_str)
        self.logger.debug(f"send: {sub_str}")
        for _ in range(len(self.channels)):
            res = await self.ws.recv()
            self.logger.debug(f"recv: {res}")
        await self.ws.close()

    async def __aiter__(self):
        """AsyncGenerator of Websocket stream"""
        while True:
            try:
                res = await asyncio.wait_for(self.ws.recv(), timeout=self.ping_interval)
                res = self.process_result(res)
                if res:
                    yield res
            except (asyncio.TimeoutError, ConnectionClosed):
                try:
                    await self.ws.send("ping")
                    res = await self.ws.recv()
                    self.logger.debug(res)
                except Exception as exc:
                    self.logger.debug("Connection closed", exc_info=exc)
                    break
        await self.unsubscribe()

    @staticmethod
    def process_result(res):
        jres = json.loads(res)
        if "event" not in jres:
            return jres


class PrivateSubscription(PublicSubscription):
    def __init__(self, uri, channels: Sequence[Channel], api_key, api_secret_key, passphrase, **ws_kwargs):
        super().__init__(uri, channels, **ws_kwargs)
        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.passphrase = passphrase

    def login_params(self):
        timestamp = get_local_timestamp()
        sign = signature(timestamp, "GET", "/users/self/verify", "", self.api_secret_key)
        login_params = {
            "op": "login",
            "args": [
                {
                    "apiKey": self.api_key,
                    "passphrase": self.passphrase,
                    "timestamp": timestamp,
                    "sign": sign.decode("utf-8"),
                }
            ],
        }
        login_str = json.dumps(login_params)
        return login_str

    LOGIN_SEMAPHORE = RateLimiter(1, 1)

    async def subscribe(self):
        try:
            self.ws = await connect(self.uri, **self.ws_kwargs)
            login_str = self.login_params()
            async with self.LOGIN_SEMAPHORE:
                await self.ws.send(login_str)
            self.logger.debug(f"send: {login_str}")
            res = await self.ws.recv()
            self.logger.debug(res)
            sub_params = {"op": "subscribe", "args": self.channels}
            sub_str = json.dumps(sub_params)
            async with self.SUBSCRIPTION_SEMAPHORE:
                await self.ws.send(sub_str)
            self.logger.debug(f"send: {sub_str}")
        except Exception as exc:
            self.logger.error(f"Websocket subscribe error", exc_info=exc)


class OkxWebsocket:
    logger = logging.getLogger("OkxWebsocket")
    logger.setLevel(logging.DEBUG)

    def __init__(self, api_key, api_secret_key, passphrase, test=False):
        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.passphrase = passphrase
        self.test = test

    def public_uri(self, channels: Sequence[PublicChannel]) -> str:
        public_uri = TEST_WS_PUBLIC_URL if self.test else WS_PUBLIC_URL
        biz_url = TEST_WS_BIZ_URL if self.test else WS_BIZ_URL
        return biz_url if any(channel["channel"] in BUSINESS_CHANNELS for channel in channels) else public_uri

    def private_uri(self, channels: Sequence[PrivateChannel]) -> str:
        private_uri = TEST_WS_PRIVATE_URL if self.test else WS_PRIVATE_URL
        biz_url = TEST_WS_BIZ_URL if self.test else WS_BIZ_URL
        return biz_url if any(channel["channel"] in BUSINESS_CHANNELS for channel in channels) else private_uri

    async def subscribe_public(self, channels: Sequence[PublicChannel], **ws_kwargs) -> PublicSubscription:
        """Subscribe to public channels

        Usage:
            async for res in await okx_ws.subscribe_public(channels):
                print(res)
        :param channels: list of channels to subscribe
        :param ws_kwargs: kwargs for `websockets.connect`
        :return: WebsocketSubscription `AsyncGenerator` of websocket stream
        """
        uri = self.public_uri(channels)
        ps = PublicSubscription(uri, channels, **ws_kwargs)
        await ps.subscribe()
        return ps

    async def subscribe_private(self, channels: Sequence[PrivateChannel], **ws_kwargs) -> PrivateSubscription:
        """Subscribe to private channels

        Usage:
            async for res in await okx_ws.subscribe_private(channels):
                print(res)
        :param channels: list of channels to subscribe
        :return: WebsocketSubscription `AsyncGenerator` of websocket stream
        """
        uri = self.private_uri(channels)
        ps = PrivateSubscription(uri, channels, self.api_key, self.api_secret_key, self.passphrase, **ws_kwargs)
        await ps.subscribe()
        return ps
