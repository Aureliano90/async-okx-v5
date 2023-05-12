from . import consts as c, utils, exceptions
import asyncio
from aiohttp import ClientSession, ClientTimeout, ClientError
from datetime import datetime
import json
import logging

logger = logging.getLogger('Client')
logger.setLevel(logging.DEBUG)

MAX_RETRY = 100
BACKOFF_MULTIPLIER = 1.1


class Client:
    client = ClientSession(base_url=c.API_URL, timeout=ClientTimeout(5))

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, **kwargs):
        if kwargs:
            Client.client = ClientSession(base_url=c.API_URL, **kwargs)
        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.test = test

    async def _get_timestamp(self):
        url = c.SERVER_TIMESTAMP_URL
        async with self.client.get(url) as response:
            res_json = await response.json()
            if response.status == 200:
                t = datetime.utcfromtimestamp(int(res_json['data'][0]['ts']) / 1000)
                t = t.isoformat('T', 'milliseconds')
                return f'{t}Z'
            else:
                return ''

    async def _request(self, method, request_path, params):
        if method == c.GET:
            request_path += utils.parse_params_to_str(params)

        success = False
        retry = 0
        backoff = 1
        # 处理网络异常
        while not success and retry < MAX_RETRY:
            try:
                # sign & header
                if self.use_server_time:
                    # 获取服务器时间
                    timestamp = await self._get_timestamp()
                else:
                    # 获取本地时间
                    timestamp = utils.get_timestamp()

                body = json.dumps(params) if method == c.POST else ''
                sign = utils.sign(utils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
                header = utils.get_header(self.API_KEY, sign.decode('utf8'), timestamp, self.PASSPHRASE)

                if self.test:
                    header['x-simulated-trading'] = '1'

                # send request
                if method == c.GET:
                    try:
                        response = await self.client.get(request_path, headers=header)
                    except (ClientError, asyncio.TimeoutError):
                        retry += 1
                        continue
                elif method == c.POST:
                    response = await self.client.post(request_path, data=body, headers=header)
                elif method == c.DELETE:
                    response = await self.client.delete(request_path, headers=header)
                else:
                    raise ValueError
            except (ClientError, asyncio.TimeoutError) as exc:
                logger.debug('Network error', exc_info=exc)
                await asyncio.sleep(backoff)
                retry += 1
                backoff *= BACKOFF_MULTIPLIER
                continue
            else:
                async with response:
                    status = response.status
                    # Cloudflare error
                    if str(status).startswith('5'):
                        logger.debug(f'Cloudflare error {response}')
                        await asyncio.sleep(backoff)
                        retry += 1
                        backoff *= BACKOFF_MULTIPLIER
                        continue
                    try:
                        json_res = await response.json()
                    except asyncio.TimeoutError:
                        retry += 1
                        continue
                    except ValueError:
                        text = await response.text()
                        if 'cloudflare' in text:
                            await asyncio.sleep(backoff)
                            retry += 1
                            backoff *= BACKOFF_MULTIPLIER
                            continue
                        raise exceptions.OkexRequestException(f'Invalid Response: {text}')
                    # Endpoint request timeout
                    if json_res.get('code') == '50004':
                        retry += 1
                        await asyncio.sleep(2)
                        continue
                    # Requests too frequent
                    if status == 429:
                        retry += 1
                        logger.debug(f"{request_path}, {json_res['msg']}")
                        await asyncio.sleep(2)
                        continue
                    success = True

                    # exception handle
                    if not str(status).startswith('2'):
                        logger.error(f"{json_res['code']}: {json_res['msg']}")
                        logger.error(f'Client error {status}: {request_path}')
                        raise exceptions.OkexAPIException(status, text, json_res)
        return json_res

    async def _request_without_params(self, method, request_path):
        return await self._request(method, request_path, {})

    async def _request_with_params(self, method, request_path, params):
        return await self._request(method, request_path, params)
