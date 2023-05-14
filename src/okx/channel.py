from .types import *


class Channel(TypedDict):
    pass


class PublicChannel(Channel):
    pass


class PrivateChannel(Channel):
    pass


class InstrumentsChannel(PublicChannel):
    channel: Literal['instruments']
    instType: InstType


class TickersChannel(PublicChannel):
    channel: Literal['tickers']
    instId: str


class OpenInterestChannel(PublicChannel):
    channel: Literal['open-interest']
    instId: str


class CandleChannel(PublicChannel):
    channel: Literal[
        'candle3M', 'candle1M', 'candle1W', 'candle1D', 'candle2D', 'candle3D', 'candle5D', 'candle12H',
        'candle6H', 'candle4H', 'candle2H', 'candle1H', 'candle30m', 'candle15m', 'candle5m', 'candle3m',
        'candle1m', 'candle3Mutc', 'candle1Mutc', 'candle1Wutc', 'candle1Dutc', 'candle2Dutc',
        'candle3Dutc', 'candle5Dutc', 'candle12Hutc', 'candle6Hutc']
    instId: str


class TradesChannel(PublicChannel):
    channel: Literal['trades']
    instId: str


class OptionsChannel(PublicChannel):
    channel: Literal['opt-summary']
    instId: Literal['BTC-USD', 'ETH-USD']


class FundingRateChannel(PublicChannel):
    channel: Literal['funding-rate']
    instId: str


class AccountChannel(PrivateChannel, total=False):
    channel: Literal['account']
    ccy: str


class PositionsChannel(PrivateChannel, total=False):
    channel: Literal['positions']
    instType: InstType
    instFamily: str
    instId: str


class BalanceAndPositionChannel(PrivateChannel):
    channel: Literal['balance_and_position']


class OrdersChannel(PrivateChannel, total=False):
    channel: Literal['orders']
    instType: InstType
    instFamily: str
    instId: str


class AccountGreeksChannel(PrivateChannel, total=False):
    channel: Literal['account-greeks']
    ccy: str


class DepositInfoChannel(PrivateChannel, total=False):
    channel: Literal['deposit-info']
    ccy: str


class WithdrawalInfoChannel(PrivateChannel, total=False):
    channel: Literal['withdrawal-info']
    ccy: str


BUSINESS_CHANNELS = {'deposit-info', 'withdrawal-info', 'candle3M', 'candle1M', 'candle1W', 'candle1D', 'candle2D',
                     'candle3D', 'candle5D', 'candle12H', 'candle6H', 'candle4H', 'candle2H', 'candle1H', 'candle30m',
                     'candle15m', 'candle5m', 'candle3m', 'candle1m', 'candle3Mutc', 'candle1Mutc', 'candle1Wutc',
                     'candle1Dutc', 'candle2Dutc', 'candle3Dutc', 'candle5Dutc', 'candle12Hutc', 'candle6Hutc'}
