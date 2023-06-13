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


async def query_with_pagination(query_api, tag, page_size, count=0, interval=0, **kwargs):
    """Loop `api` until `limit` is reached

    :param query_api: api coroutine with `after` and `limit` keyword arguments
    :param tag: tag used by `after` argument
    :param page_size: max number of results in a single request
    :param count: number of entries
    :param interval: time interval between entries in milliseconds
    :param kwargs: other arguments
    :return: List
    """
    # Number of entries is known.
    if count > 0:
        # First time
        if count < page_size:
            return await query_api(**kwargs, limit=count)
        else:
            res = temp = await query_api(**kwargs, limit=page_size)
            count -= page_size
        # Parallelize if time interval is known
        if interval:
            after = int(temp[-1][tag])
            tasks = []
            while count > 0:
                if count < page_size:
                    tasks.append(query_api(**kwargs, after=after, limit=count))
                else:
                    tasks.append(query_api(**kwargs, after=after, limit=page_size))
                after -= page_size * interval
                count -= page_size
            for temp in await asyncio.gather(*tasks):
                res.extend(temp)
        else:
            while count > 0:
                if count < page_size:
                    temp = await query_api(**kwargs, after=temp[page_size - 1][tag], limit=count)
                else:
                    temp = await query_api(**kwargs, after=temp[page_size - 1][tag], limit=page_size)
                res.extend(temp)
                count -= page_size
    else:
        # First time
        res = temp = await query_api(**kwargs)
        # Results not exhausted
        while len(temp) == page_size:
            temp = await query_api(**kwargs, after=temp[page_size - 1][tag])
            res.extend(temp)
    return res
