from .client import OkxClient
from .consts import *
from .types import *
from .utils import RateLimiter
import logging


class AccountAPI(OkxClient):
    logger = logging.getLogger("AccountAPI")
    logger.setLevel(logging.DEBUG)

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, **kwargs):
        super(AccountAPI, self).__init__(api_key, api_secret_key, passphrase, use_server_time, test, **kwargs)

    ACCOUNT_CONFIG_SEMAPHORE = RateLimiter(5, 2)

    async def get_account_config(self) -> AccountConfigResponse:
        """查看当前账户的配置信息

        GET /api/v5/account/config 限速：5次/2s
        """
        async with self.ACCOUNT_CONFIG_SEMAPHORE:
            res = await self._request_without_params(GET, ACCOUNT_CONFIG)
        assert res["code"] == "0", f"{ACCOUNT_CONFIG}, msg={res['msg']}"
        return res["data"][0]

    POSITION_MODE_SEMAPHORE = RateLimiter(5, 2)

    async def set_position_mode(self, posMode: Literal["long_short_mode", "net_mode"]) -> PosModeResponse:
        """设置持仓模式

        POST /api/v5/account/set-position-mode 限速：5次/2s

        :param posMode: 持仓方式 long_short_mode：双向持仓 net_mode：单向持仓
        """
        params = dict(posMode=posMode)
        async with self.POSITION_MODE_SEMAPHORE:
            res = await self._request_with_params(POST, POSITION_MODE, params)
        assert res["code"] == "0", f"{POSITION_MODE}, msg={res['msg']}"
        return res["data"][0]

    ACCOUNT_POSITION_SEMAPHORE = RateLimiter(10, 2)

    async def get_positions(
        self, instType: Literal["MARGIN", "SWAP", "FUTURES", "OPTION"] = None, instId=None, posId=None
    ) -> List[Dict]:
        """查看持仓信息

        GET /api/v5/account/positions 限速：10次/2s

        :param instType: MARGIN：币币杠杆 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param instId: 交易产品ID，支持多个instId查询（不超过10个），半角逗号分隔
        :param posId: 持仓ID，支持多个posId查询（不超过20个），半角逗号分隔
        """
        if instType:
            params = dict(instType=instType)
        elif instId:
            if not type(instId) is str:
                assert len(instId) <= 10
                instId = ",".join(instId)
            params = dict(instId=instId)
        else:
            if not type(posId) is str:
                assert len(posId) <= 20
                posId = ",".join(posId)
            params = dict(posId=posId)
        async with self.ACCOUNT_POSITION_SEMAPHORE:
            res = await self._request_with_params(GET, ACCOUNT_POSITION, params)
        assert res["code"] == "0", f"{ACCOUNT_POSITION}, msg={res['msg']}"
        return res["data"]

    async def get_specific_position(self, instId="", posId="") -> List[Dict]:
        """查看持仓信息

        GET /api/v5/account/positions?instId=BTC-USDT

        :param instId: 产品ID
        :param posId: 持仓ID
        """
        params = dict(instId=instId) if instId else dict(posId=posId)
        async with self.ACCOUNT_POSITION_SEMAPHORE:
            res = await self._request_with_params(GET, ACCOUNT_POSITION, params)
        assert res["code"] == "0", f"{ACCOUNT_POSITION}, msg={res['msg']}"
        return res["data"]

    ACCOUNT_BALANCE_SEMAPHORE = RateLimiter(10, 2)

    async def get_account_balance(self) -> Dict:
        """获取账户中所有资产余额

        GET /api/v5/account/balance 限速： 10次/2s
        """
        async with self.ACCOUNT_BALANCE_SEMAPHORE:
            res = await self._request_without_params(GET, ACCOUNT_BALANCE)
        assert res["code"] == "0", f"{ACCOUNT_BALANCE}, msg={res['msg']}"
        return res["data"][0]

    async def get_coin_balance(self, ccy) -> Dict:
        """获取账户中单币种余额

        GET /api/v5/account/balance?ccy=BTC,ETH

        :param ccy: 币种，如 BTC，支持多币种查询（不超过20个），币种之间半角逗号分隔
        """
        if not type(ccy) is str:
            assert len(ccy) <= 20
            ccy = ",".join(ccy)
        params = dict(ccy=ccy)
        async with self.ACCOUNT_BALANCE_SEMAPHORE:
            res = await self._request_with_params(GET, ACCOUNT_BALANCE, params)
        assert res["code"] == "0", f"{ACCOUNT_BALANCE}, msg={res['msg']}"
        return res["data"][0]

    TRADE_FEE_SEMAPHORE = RateLimiter(5, 2)

    async def get_trade_fee(self, instType, instId="", uly="", category="") -> Dict:
        """获取当前账户交易手续费费率

        GET /api/v5/account/trade-fee 限速：5次/2s

        :param instType: SPOT：币币 MARGIN：币币杠杆 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param instId: 产品ID，仅适用于instType为币币/币币杠杆
        :param uly: 合约标的指数，仅适用于instType为交割/永续/期权
        :param category: 手续费档位
        """
        params = dict(instId=instId) if instId else dict(uly=uly) if uly else dict(category=category)
        params["instType"] = instType
        async with self.TRADE_FEE_SEMAPHORE:
            res = await self._request_with_params(GET, TRADE_FEE, params)
        assert res["code"] == "0", f"{TRADE_FEE}, msg={res['msg']}"
        return res["data"][0]

    GET_LEVERAGE_SEMAPHORE = RateLimiter(20, 2)

    async def get_leverage(self, instId, mgnMode) -> Dict:
        """获取杠杆倍数

        GET /api/v5/account/leverage-info 限速：20次/2s

        :param instId: 产品ID
        :param mgnMode: 保证金模式 isolated：逐仓 cross：全仓
        """
        params = dict(instId=instId, mgnMode=mgnMode)
        async with self.GET_LEVERAGE_SEMAPHORE:
            res = await self._request_with_params(GET, GET_LEVERAGE, params)
        assert res["code"] == "0", f"{GET_LEVERAGE}, msg={res['msg']}"
        return res["data"][0]

    SET_LEVERAGE_SEMAPHORE = RateLimiter(20, 2)

    async def set_leverage(self, lever, mgnMode, instId="", ccy="", posSide="") -> Dict:
        """设置杠杆倍数

        POST /api/v5/account/set-leverage 限速：20次/2s

        :param instId: 产品ID：币对、合约
        :param ccy: 保证金币种
        :param lever: 杠杆倍数
        :param mgnMode: 保证金模式 isolated：逐仓 cross：全仓
        :param posSide: 持仓方向
        """
        if instId:
            params = dict(lever=lever, mgnMode=mgnMode, instId=instId)
        else:
            params = dict(lever=lever, mgnMode=mgnMode, ccy=ccy)
        if posSide:
            params["posSide"] = posSide
        async with self.SET_LEVERAGE_SEMAPHORE:
            res = await self._request_with_params(POST, SET_LEVERAGE, params)
        assert res["code"] == "0", f"{SET_LEVERAGE}, msg={res['msg']}"
        return res["data"][0]

    MAX_SIZE_SEMAPHORE = RateLimiter(20, 2)

    async def get_max_size(self, instId, tdMode, ccy="", px="", leverage="") -> Dict:
        """获取最大可买卖/开仓数量

        GET /api/v5/account/max-size 限速：20次/2s

        :param instId: 产品ID
        :param tdMode: 交易模式 cross：全仓 isolated：逐仓 cash：非保证金
        :param ccy: 保证金币种
        :param px: 委托价格
        :param leverage: 开仓杠杆倍数
        """
        params = dict(instId=instId, tdMode=tdMode)
        if ccy:
            params["ccy"] = ccy
        if ccy:
            params["px"] = px
        if ccy:
            params["leverage"] = leverage
        async with self.MAX_SIZE_SEMAPHORE:
            res = await self._request_with_params(GET, MAX_SIZE, params)
        assert res["code"] == "0", f"{MAX_SIZE}, msg={res['msg']}"
        return res["data"][0]

    GET_LEDGER_SEMAPHORE = RateLimiter(5, 1)

    async def get_ledger(
        self, instType, ccy, mgnMode="", ctType="", type="", subType="", after="", before="", limit=""
    ) -> List[Dict]:
        """账单流水查询

        GET /api/v5/account/bills 限速：5次/s

        :param instType: 产品类型 SPOT：币币 MARGIN：币币杠杆 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param ccy: 币种
        :param mgnMode: 仓位类型 isolated：逐仓 cross：全仓
        :param ctType: linear： 正向合约 inverse： 反向合约
        :param type: 账单类型 1：划转 2：交易 3：交割 4：自动换币 5：强平 6：保证金划转 7：扣息 8：资金费 9：自动减仓 10：穿仓补偿
                            11：系统换币 12：策略划拨 13：对冲减仓
        :param subType: 账单子类型
        :param after: 请求此id之前
        :param before: 请求此id之后
        :param limit: 分页返回的结果集数量，最大为100，不填默认返回100条
        """
        params = dict(
            instType=instType,
            ccy=ccy,
            mgnMode=mgnMode,
            ctType=ctType,
            type=type,
            subType=subType,
            after=after,
            before=before,
            limit=limit,
        )
        async with self.GET_LEDGER_SEMAPHORE:
            res = await self._request_with_params(GET, GET_LEDGER, params)
        assert res["code"] == "0", f"{GET_LEDGER}, msg={res['msg']}"
        return res["data"]

    ARCHIVE_LEDGER_SEMAPHORE = RateLimiter(5, 2)

    async def get_archive_ledger(
        self, instType, ccy, mgnMode="", ctType="", type="", subType="", after="", before="", limit=""
    ) -> List[Dict]:
        """账单流水查询

        GET /api/v5/account/bills-archive 限速：5次/2s

        :param instType: 产品类型 SPOT：币币 MARGIN：币币杠杆 SWAP：永续合约 FUTURES：交割合约 OPTION：期权
        :param ccy: 币种
        :param mgnMode: 仓位类型 isolated：逐仓 cross：全仓
        :param ctType: linear： 正向合约 inverse： 反向合约
        :param type: 账单类型 1：划转 2：交易 3：交割 4：自动换币 5：强平 6：保证金划转 7：扣息 8：资金费 9：自动减仓 10：穿仓补偿
                            11：系统换币 12：策略划拨 13：对冲减仓
        :param subType: 账单子类型
        :param after: 请求此id之前
        :param before: 请求此id之后
        :param limit: 分页返回的结果集数量，最大为100，不填默认返回100条
        """
        params = dict(
            instType=instType,
            ccy=ccy,
            mgnMode=mgnMode,
            ctType=ctType,
            type=type,
            subType=subType,
            after=after,
            before=before,
            limit=limit,
        )
        async with self.ARCHIVE_LEDGER_SEMAPHORE:
            res = await self._request_with_params(GET, GET_ARCHIVE_LEDGER, params)
        assert res["code"] == "0", f"{GET_ARCHIVE_LEDGER}, msg={res['msg']}"
        return res["data"]

    MARGIN_BALANCE_SEMAPHORE = RateLimiter(20, 2)

    async def adjust_margin(self, instId, posSide, type, amt):
        """增加或者减少逐仓保证金

        POST /api/v5/account/position/margin-balance 限速：20次/2s

        :param instId: 产品ID
        :param posSide: 持仓方向 long：双向持仓多头 short：双向持仓空头 net：单向持仓
        :param type: add：增加 reduce：减少
        :param amt: 增加或减少的保证金数量
        :rtype: bool
        """
        params = dict(instId=instId, posSide=posSide, type=type, amt=amt)
        async with self.MARGIN_BALANCE_SEMAPHORE:
            res = await self._request_with_params(POST, MARGIN_BALANCE, params)
        if res["code"] == "0":
            return True
        else:
            self.logger.warning(f"{MARGIN_BALANCE}, msg={res['msg']}")
            return False
