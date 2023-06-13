import asyncio
import pytest
from async_okx_v5.public import PublicAPI


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_get_instruments():
    response = await PublicAPI().get_instruments("SWAP", "BTC-USD")
    assert isinstance(response, list)
    assert len(response) > 0
    assert isinstance(response[0], dict)
    assert "instType" in response[0]
    assert "instId" in response[0]


@pytest.mark.asyncio
async def test_get_specific_instrument():
    response = await PublicAPI().get_specific_instrument("SPOT", "BTC-USDT")
    assert isinstance(response, dict)
    assert response["instId"] == "BTC-USDT"


@pytest.mark.asyncio
async def test_get_funding_time():
    response = await PublicAPI().get_funding_time("BTC-USDT-SWAP")
    assert isinstance(response, dict)
    assert "instId" in response
    assert "fundingRate" in response
    assert response["instId"] == "BTC-USDT-SWAP"


@pytest.mark.asyncio
async def test_get_historical_funding_rate():
    response = await PublicAPI().get_historical_funding_rate("BTC-USDT-SWAP")
    assert isinstance(response, list)
    assert isinstance(response[0], dict)
    assert "instId" in response[0]
    assert "fundingRate" in response[0]
    assert response[0]["instId"] == "BTC-USDT-SWAP"


@pytest.mark.asyncio
async def test_get_funding_history():
    response = await PublicAPI().get_funding_history("BTC-USDT-SWAP")
    assert isinstance(response, list)
    assert isinstance(response[0], dict)
    assert "instId" in response[0]
    assert "fundingRate" in response[0]
    assert response[0]["instId"] == "BTC-USDT-SWAP"


@pytest.mark.asyncio
async def test_get_tickers():
    response = await PublicAPI().get_tickers("SWAP", "BTC-USD")
    assert isinstance(response, list)
    assert len(response) > 0
    assert isinstance(response[0], dict)
    assert "instType" in response[0]
    assert "instId" in response[0]


@pytest.mark.asyncio
async def test_get_specific_ticker():
    response = await PublicAPI().get_specific_ticker("BTC-USDT-SWAP")
    assert isinstance(response, dict)
    assert response["instId"] == "BTC-USDT-SWAP"


@pytest.mark.asyncio
async def test_get_candles():
    response = await PublicAPI().get_candles("BTC-USDT-SWAP", "4H")
    assert isinstance(response, list)
    assert len(response) > 0
    assert isinstance(response[0], tuple)
    assert len(response[0]) > 0


@pytest.mark.asyncio
async def test_history_candles():
    response = await PublicAPI().history_candles("BTC-USDT-SWAP", "4H")
    assert isinstance(response, list)
    assert len(response) > 0
    assert isinstance(response[0], tuple)
    assert len(response[0]) > 0


@pytest.mark.asyncio
async def test_get_candles_for_days():
    response = await PublicAPI().get_candles_for_days("BTC-USDT-SWAP", 10, "4H")
    assert isinstance(response, list)
    assert len(response) > 0
    assert isinstance(response[0], tuple)
    assert len(response[0]) > 0
