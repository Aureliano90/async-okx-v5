import asyncio
from .client import OkxClient
from .consts import *
from .exceptions import *
from .types import *
from .utils import RateLimiter, query_with_pagination
import logging


class PublicAPI(OkxClient):
    logger = logging.getLogger("PublicAPI")
    logger.setLevel(logging.DEBUG)

    def __init__(self, use_server_time=False, test=False, **kwargs):
        super(PublicAPI, self).__init__("", "", "", use_server_time, test, **kwargs)

    GET_INSTRUMENTS_SEMAPHORE = dict()

    async def get_instruments(self, instType: InstType, instFamily="") -> List[dict]:
        """获取所有可交易产品的信息列表

        GET /api/v5/public/instruments?instType=SWAP

        限速： 20次/2s 限速规则：IP +instType

        :param instType: SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param instFamily: 交易品种，仅适用于交割/永续/期权
        """
        params = dict(instType=instType)
        if instFamily:
            params["instFamily"] = instFamily
        if instType not in PublicAPI.GET_INSTRUMENTS_SEMAPHORE.keys():
            PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType] = RateLimiter(20, 2)
        async with PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType]:
            res = await self._request_with_params(GET, GET_INSTRUMENTS, params)
        assert res["code"] == "0", f"{GET_INSTRUMENTS}, msg={res['msg']}"
        return res["data"]

    async def get_specific_instrument(self, instType: InstType, instId: str, uly="") -> dict:
        """获取单个可交易产品的信息

        GET /api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP

        :param instType: SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param uly: 合约标的指数，仅适用于交割/永续/期权，期权必填
        :param instId: 产品ID
        """
        params = dict(instType=instType, instId=instId)
        if uly:
            params["uly"] = uly
        if instType not in PublicAPI.GET_INSTRUMENTS_SEMAPHORE.keys():
            PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType] = RateLimiter(20, 2)
        async with PublicAPI.GET_INSTRUMENTS_SEMAPHORE[instType]:
            res = await self._request_with_params(GET, GET_INSTRUMENTS, params)
        if res["code"] == "51001":
            raise OkexRequestException(res["msg"])
        return res["data"][0]

    async def get_funding_time(self, instId: str) -> FundingRateResponse:
        """获取当前资金费率

        GET /api/v5/public/funding-rate?instId=BTC-USD-SWAP

        限速： 20次/2s 限速规则：IP +instrumentID

        :param instId: 产品ID，如 BTC-USD-SWAP
        """
        params = dict(instId=instId)
        res = await self._request_with_params(GET, FUNDING_RATE, params)
        assert res["code"] == "0", f"{FUNDING_RATE}, msg={res['msg']}"
        return res["data"][0]

    async def get_historical_funding_rate(
        self, instId: str, after="", before="", limit=""
    ) -> List[FundingRateResponse]:
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
        assert res["code"] == "0", f"{FUNDING_RATE_HISTORY}, msg={res['msg']}"
        return res["data"]

    async def get_funding_history(self, instId, count=270):
        """下载最近3个月资金费率"""
        return await query_with_pagination(
            self.get_historical_funding_rate,
            tag="fundingTime",
            page_size=100,
            count=count,
            interval=28800000,
            instId=instId,
        )

    GET_TICKERS_SEMAPHORE = RateLimiter(20, 2)

    async def get_tickers(self, instType: InstType, uly="") -> List[TickerResponse]:
        """获取所有产品行情信息

        GET /api/v5/market/tickers?instType=SWAP 限速： 20次/2s

        :param instType: 产品类型，SPOT：币币 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param uly: 标的指数，仅适用于交割/永续/期权
        """
        params = dict(instType=instType)
        if uly:
            params["uly"] = uly
        while True:
            try:
                async with self.GET_TICKERS_SEMAPHORE:
                    return (await self._request_with_params(GET, GET_TICKERS, params))["data"]
            except OkexAPIException:
                await asyncio.sleep(10)

    GET_TICKER_SEMAPHORE = RateLimiter(20, 2)

    async def get_specific_ticker(self, instId: str) -> TickerResponse:
        """获取单个产品行情信息

        GET /api/v5/market/ticker?instId=BTC-USD-SWAP 限速： 20次/2s

        :param instId: 产品ID
        """
        params = dict(instId=instId)
        while True:
            try:
                async with self.GET_TICKER_SEMAPHORE:
                    return (await self._request_with_params(GET, GET_TICKER, params))["data"][0]
            except OkexAPIException:
                await asyncio.sleep(10)

    GET_CANDLES_SEMAPHORE = RateLimiter(40, 2)

    async def get_candles(self, instId: str, bar: Bar = "4H", after="", before="", limit="") -> List[Candle]:
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
        assert res["code"] == "0", f"{GET_CANDLES}, msg={res['msg']}"
        return [Candle(*candle) for candle in res["data"]]

    HISTORY_CANDLES_SEMAPHORE = RateLimiter(20, 2)

    async def history_candles(self, instId: str, bar: Bar = "4H", after="", before="", limit="") -> List[Candle]:
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
        assert res["code"] == "0", f"{HISTORY_CANDLES}, msg={res['msg']}"
        return [Candle(*candle) for candle in res["data"]]

    async def get_candles_for_days(self, instId: str, days: int, bar: Bar = "4H") -> List[Candle]:
        """获取最近K线

        :param instId: 产品ID
        :param days: 最近几天
        :param bar: 时间粒度，默认值1m，如 [1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M/3M/6M/1Y]
        """
        interval = 0
        if bar.endswith("m"):
            count = days * 1440 // int(bar[:-1]) + 1
            interval = int(bar[:-1]) * 60000
        elif bar.endswith("H"):
            count = days * 24 // int(bar[:-1]) + 1
            interval = int(bar[:-1]) * 3600000
        elif bar.endswith("D"):
            count = days + 1
            interval = int(bar[:-1]) * 86400000
        elif bar.endswith("W"):
            count = days // 7 + 1
            interval = int(bar[:-1]) * 604800000
        elif bar.endswith("M"):
            count = days // (30 * int(bar[:-1])) + 1
        else:
            count = days // 365 + 1
        if count > 1440:
            return await query_with_pagination(
                self.history_candles,
                tag=0,
                page_size=100,
                count=count,
                interval=interval,
                instId=instId,
                bar=bar,
            )
        else:
            return await query_with_pagination(
                self.get_candles, tag=0, page_size=300, count=count, interval=interval, instId=instId, bar=bar
            )
