from typing import Dict, List, Literal, NamedTuple, Sequence, TypedDict


class AccountConfigResponse(TypedDict):
    uid: str
    # acctLv	String	账户层级
    # 1：简单交易模式，2：单币种保证金模式 ，3：跨币种保证金模式 ，4：组合保证金模式
    acctLv: str
    # posMode	String	持仓方式
    # long_short_mode：双向持仓 net_mode：单向持仓
    posMode: str
    autoLoan: bool
    greeksType: str
    level: str
    levelTmp: str
    ctIsoMode: str
    mgnIsoMode: str
    spotOffsetType: str
    label: str
    roleType: str
    traderInsts: List
    opAuth: str
    ip: str


class PosModeResponse(TypedDict):
    posMode: Literal['long_short_mode', 'net_mode']


class AssetBalanceResponse(TypedDict):
    """账户余额
    :param ccy: 币种，如 BTC
    :param bal: 余额
    :param frozenBal: 冻结余额
    :param availBal: 可用余额
    """
    ccy: str
    bal: str
    frozenBal: str
    availBal: str


AssetTransferResponse = TypedDict('AssetTransferResponse', {
    'transId': str,  # 划转 ID
    'ccy': str,  # 划转币种
    'from': str,  # 转出账户
    'amt': str,  # 划转量
    'to': str,  # 转入账户
    'clientId': str  # 客户自定义ID
})

InstType = Literal['SPOT', 'SWAP', 'FUTURES', 'OPTION']

Bar = Literal['1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', '6H', '12H', '1D', '1W', '1M', '3M', '6M', '1Y']


class Candle(NamedTuple):
    """K线数据
    :param ts: 开始时间，Unix时间戳的毫秒数格式，如 1597026383085
    :param o: 开盘价格
    :param h: 最高价格
    :param l: 最低价格
    :param c: 收盘价格
    :param vol: 交易量，以张为单位
        如果是衍生品合约，数值为合约的张数。
        如果是币币/币币杠杆，数值为交易货币的数量。
    :param volCcy: 交易量，以币为单位
        如果是衍生品合约，数值为交易货币的数量。
        如果是币币/币币杠杆，数值为计价货币的数量。
    :param volCcyQuote: 交易量，以计价货币为单位
        如：BTC-USDT 和 BTC-USDT-SWAP, 单位均是 USDT；
        BTC-USD-SWAP 单位是 USD
    :param confirm: K线状态
        0 代表 K 线未完结，1 代表 K 线已完结。
    """
    ts: str
    o: str
    h: str
    l: str
    c: str
    vol: str
    volCcy: str
    volCcyQuote: str
    confirm: str
