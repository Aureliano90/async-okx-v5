from .client import OkxClient
from .consts import *
from .types import *
from .utils import RateLimiter
import logging


class AssetAPI(OkxClient):
    logger = logging.getLogger("AssetAPI")
    logger.setLevel(logging.DEBUG)

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, **kwargs):
        super(AssetAPI, self).__init__(api_key, api_secret_key, passphrase, use_server_time, test, **kwargs)

    ASSET_BALANCE_SEMAPHORE = RateLimiter(6, 1)

    async def get_balance(self, ccy: Sequence[str]) -> AssetBalanceResponse:
        """获取资金账户余额信息

        GET /api/v5/asset/balances 限速： 6次/s

        :param ccy: 币种，支持多币种查询（不超过20个），币种之间半角逗号分隔
        """
        if not type(ccy) is str:
            assert len(ccy) <= 20
            ccy = ",".join(ccy)
        params = dict(ccy=ccy)
        async with self.ASSET_BALANCE_SEMAPHORE:
            res = await self._request_with_params(GET, ASSET_BALANCE, params)
        assert res["code"] == "0", f"{ASSET_BALANCE}, msg={res['msg']}"
        return res["data"][0]

    ASSET_TRANSFER_SEMAPHORE = dict()

    async def transfer(self, ccy, amt, account_from, account_to, instId="", toInstId="") -> AssetTransferResponse:
        """资金划转

        POST /api/v5/asset/transfer

        限速： 1 次/s 限速规则：UserID + Currency

        :param ccy: 币种
        :param amt: 划转数量
        :param account_from: 转出账户 6：资金账户 18：统一账户
        :param account_to: 转入账户 6：资金账户 18：统一账户
        :param instId:
        :param toInstId:
        """
        params = {"ccy": ccy, "amt": amt, "from": account_from, "to": account_to}
        if instId:
            params["instId"] = instId
        if toInstId:
            params["toInstId"] = toInstId
        if ccy not in AssetAPI.ASSET_TRANSFER_SEMAPHORE.keys():
            AssetAPI.ASSET_TRANSFER_SEMAPHORE[ccy] = RateLimiter(1, 1)
        async with AssetAPI.ASSET_TRANSFER_SEMAPHORE[ccy]:
            res = await self._request_with_params(POST, ASSET_TRANSFER, params)
        if res["code"] == "0":
            return res["data"][0]
        else:
            self.logger.warning(f"{ASSET_TRANSFER}, msg={res['msg']}")
            raise Exception(f"{ASSET_TRANSFER}, msg={res['msg']}")
