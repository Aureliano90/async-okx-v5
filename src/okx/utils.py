import asyncio
import base64
import collections
import datetime
import hmac
import time
from . import consts as c


class RateLimiter(asyncio.Semaphore):
    """A custom semaphore to be used with REST API with velocity limit under asyncio"""

    def __init__(self, concurrency: int, interval: int):
        """控制REST API访问速率

        :param concurrency: API limit
        :param interval: Reset interval
        """
        super().__init__(concurrency)
        # Queue of inquiry timestamps
        self._inquiries = collections.deque(maxlen=concurrency)
        self._loop = asyncio.get_event_loop()
        self._concurrency = concurrency
        self._interval = interval
        self._count = concurrency

    def __repr__(self):
        return f"Rate limit: {self._concurrency} inquiries/{self._interval}s"

    async def acquire(self):
        await super().acquire()
        if self._count > 0:
            self._count -= 1
        else:
            timelapse = time.monotonic() - self._inquiries.popleft()
            # Wait until interval has passed since the first inquiry in queue returned.
            if timelapse < self._interval:
                await asyncio.sleep(self._interval - timelapse)
        return True

    def release(self):
        self._inquiries.append(time.monotonic())
        super().release()


def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding="utf8"), bytes(message, encoding="utf8"), digestmod="sha256")
    d = mac.digest()
    return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body):
    return f"{timestamp}{str.upper(method)}{request_path}{body}"


def get_header(api_key, header_sign, timestamp, passphrase):
    return {
        c.CONTENT_TYPE: c.APPLICATION_JSON,
        c.OK_ACCESS_KEY: api_key,
        c.OK_ACCESS_SIGN: header_sign,
        c.OK_ACCESS_TIMESTAMP: str(timestamp),
        c.OK_ACCESS_PASSPHRASE: passphrase,
    }


def parse_params_to_str(params):
    return "" if not params else "?" + "&".join([f"{key}={value}" for key, value in params.items()])


def get_timestamp():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return f"{t}Z"


def signature(timestamp, method, request_path, body, secret_key):
    if str(body) == "{}" or str(body) == "None":
        body = ""
    message = f"{timestamp}{method.upper()}{request_path}{body}"
    mac = hmac.new(bytes(secret_key, encoding="utf8"), bytes(message, encoding="utf8"), digestmod="sha256")
    d = mac.digest()
    return base64.b64encode(d)
