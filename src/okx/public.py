import asyncio
from typing import List, Literal, NamedTuple, Sequence, TypedDict
from .client import Client
from .consts import *
from .exceptions import *
from .utils import RateLimiter
import logging

logger = logging.getLogger('PublicAPI')
logger.setLevel(logging.DEBUG)


class PublicAPI(Client):
    def __init__(self, use_server_time=False, test=False, **kwargs):
        super(PublicAPI, self).__init__('', '', '', use_server_time, test, **kwargs)

    GET_INSTRUMENTS_SEMAPHORE = dict()

    InstType = Literal['SPOT', 'SWAP', 'FUTURES', 'OPTION']

    async def get_instruments(self, instType: InstType, instFamily='') -> List[dict]:
        """获取所有可交易产品的信息列表

        GET /api/v5/public/instruments?instType=SWAP

        限速： 20次/2s 限速规则：IP +instType

        :param instType: SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param instFamily: 交易品种，仅适用于交割/永续/期权
        """
        params = dict(instType=instType)
        if instFamily:
            params['instFamily'] = instFamily
        if instType not in PublicAPI.GET_INSTRUMENTS_SEMAPHORE.keys():
            PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType] = RateLimiter(20, 2)
        async with PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType]:
            res = await self._request_with_params(GET, GET_INSTRUMENTS, params)
        assert res['code'] == '0', f"{GET_INSTRUMENTS}, msg={res['msg']}"
        return res['data']

    async def get_specific_instrument(self, instType: InstType, instId: str, uly='') -> dict:
        """获取单个可交易产品的信息

        GET /api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP

        :param instType: SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param uly: 合约标的指数，仅适用于交割/永续/期权，期权必填
        :param instId: 产品ID
        """
        params = dict(instType=instType, instId=instId)
        if uly:
            params['uly'] = uly
        if instType not in PublicAPI.GET_INSTRUMENTS_SEMAPHORE.keys():
            PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType] = RateLimiter(20, 2)
        async with PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType]:
            res = await self._request_with_params(GET, GET_INSTRUMENTS, params)
        if res['code'] == '51001':
            raise OkexRequestException(res['msg'])
        return res['data'][0]

    async def get_funding_time(self, instId: str) -> dict:
        """获取当前资金费率

        GET /api/v5/public/funding-rate?instId=BTC-USD-SWAP

        限速： 20次/2s 限速规则：IP +instrumentID

        :param instId: 产品ID，如 BTC-USD-SWAP
        """
        params = dict(instId=instId)
        res = await self._request_with_params(GET, FUNDING_RATE, params)
        assert res['code'] == '0', f"{FUNDING_RATE}, msg={res['msg']}"
        return res['data'][0]

    async def get_historical_funding_rate(self, instId: str, after='', before='', limit='') -> List[dict]:
        """获取最近3个月的历史资金费率

        GET /api/v5/public/funding-rate-history?instId=BTC-USD-SWAP

        限速： 10次/2s 限速规则：IP +instrumentID

        :param instId: 产品ID
        :param after: 请求此时间戳之前
        :param before: 请求此时间戳之后
        :param limit: 分页返回的结果集数量，最大为100，不填默认返回100条
        """
        params = dict(instId=instId, after=after, before=before, limit=limit)
        res = await self._request_with_params(GET, FUNDING_RATE_HISTORY, params)
        assert res['code'] == '0', f"{FUNDING_RATE_HISTORY}, msg={res['msg']}"
        return res['data']

    GET_TICKERS_SEMAPHORE = RateLimiter(20, 2)

    async def get_tickers(self, instType: InstType, uly='') -> List[dict]:
        """获取所有产品行情信息

        GET /api/v5/market/tickers?instType=SWAP 限速： 20次/2s

        :param instType: 产品类型，SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param uly: 标的指数，仅适用于交割/永续/期权
        """
        params = dict(instType=instType)
        if uly:
            params['uly'] = uly
        while True:
            try:
                async with self.GET_TICKERS_SEMAPHORE:
                    return (await self._request_with_params(GET, GET_TICKERS, params))['data']
            except OkexAPIException:
                await asyncio.sleep(10)

    GET_TICKER_SEMAPHORE = RateLimiter(20, 2)

    async def get_specific_ticker(self, instId: str) -> dict:
        """获取单个产品行情信息

        GET /api/v5/market/ticker?instId=BTC-USD-SWAP 限速： 20次/2s

        :param instId: 产品ID
        """
        params = dict(instId=instId)
        while True:
            try:
                async with self.GET_TICKER_SEMAPHORE:
                    return (await self._request_with_params(GET, GET_TICKER, params))['data'][0]
            except OkexAPIException:
                await asyncio.sleep(10)

    GET_CANDLES_SEMAPHORE = RateLimiter(40, 2)

    Bar = Literal['1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', '6H', '12H', '1D', '1W', '1M', '3M', '6M', '1Y']

    # ts	String	开始时间，Unix时间戳的毫秒数格式，如 1597026383085
    # o	String	开盘价格
    # h	String	最高价格
    # l	String	最低价格
    # c	String	收盘价格
    # vol	String	交易量，以张为单位
    # 如果是衍生品合约，数值为合约的张数。
    # 如果是币币/币币杠杆，数值为交易货币的数量。
    # volCcy	String	交易量，以币为单位
    # 如果是衍生品合约，数值为交易货币的数量。
    # 如果是币币/币币杠杆，数值为计价货币的数量。
    # volCcyQuote	String	交易量，以计价货币为单位
    # 如：BTC-USDT 和 BTC-USDT-SWAP, 单位均是 USDT；
    # BTC-USD-SWAP 单位是 USD
    # confirm	String	K线状态
    # 0 代表 K 线未完结，1 代表 K 线已完结。

    class CandleResponse(NamedTuple):
        ts: str
        o: str
        h: str
        l: str
        c: str
        vol: str
        volCcy: str
        volCcyQuote: str
        confirm: str

    async def get_candles(self, instId: str, bar: Bar = '4H', after='', before='', limit='') -> List[List]:
        """获取K线数据。K线数据按请求的粒度分组返回，K线数据每个粒度最多可获取最近1440条

        GET /api/v5/market/candles 限速： 40次/2s

        :param instId: 产品ID
        :param bar: 时间粒度, [1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M/3M/6M/1Y]
        :param after: 请求此时间戳之前
        :param before: 请求此时间戳之后
        :param limit: 分页返回的结果集数量，最大为300，不填默认返回100条
        """
        params = dict(instId=instId, bar=bar, after=after, before=before, limit=limit)
        async with self.GET_CANDLES_SEMAPHORE:
            res = await self._request_with_params(GET, GET_CANDLES, params)
        assert res['code'] == '0', f"{GET_CANDLES}, msg={res['msg']}"
        return res['data']

    HISTORY_CANDLES_SEMAPHORE = RateLimiter(20, 2)

    async def history_candles(self, instId: str, bar: Bar = '4H', after='', before='', limit='') -> List[List]:
        """获取最近几年的历史k线数据

        GET /api/v5/market/history-candles 限速： 20次/2s

        :param instId: 产品ID
        :param bar: 时间粒度, [1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M/3M/6M/1Y]
        :param after: 请求此时间戳之前
        :param before: 请求此时间戳之后
        :param limit: 分页返回的结果集数量，最大为100，不填默认返回100条
        """
        params = dict(instId=instId, bar=bar, after=after, before=before, limit=limit)
        async with self.HISTORY_CANDLES_SEMAPHORE:
            res = await self._request_with_params(GET, HISTORY_CANDLES, params)
        assert res['code'] == '0', f"{HISTORY_CANDLES}, msg={res['msg']}"
        return res['data']
