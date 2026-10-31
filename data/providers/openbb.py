"""Adapter OpenBB verso il contratto interno di dati di mercato."""

from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from ..models import FundamentalMetrics, MacroObservation, PriceBar


class OpenBBProvider:
    """Normalizza lo storico OpenBB nel contratto interno.

    OpenBB è un adapter sostituibile, non il contratto del core: nessun tipo
    o namespace OpenBB deve attraversare questo modulo.
    """

    def __init__(
        self,
        client: Any | None = None,
        provider: str = "yfinance",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._client = client if client is not None else _load_openbb_client()
        self._provider = provider
        self._clock = clock

    def get_fundamental_metrics(self, symbol: str) -> FundamentalMetrics:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be blank")

        response = self._client.equity.fundamental.metrics(
            symbol=symbol,
            provider=self._provider,
        )
        rows = tuple(_rows(response))
        if not rows:
            raise ValueError(f"OpenBB returned no fundamentals for {symbol}")
        values = {
            key: None if value is None else Decimal(str(value))
            for key, value in rows[0].items()
            if key != "symbol" and (value is None or isinstance(value, (int, float)))
        }
        collected_at = self._clock()
        _require_aware_utc(collected_at, "clock result")
        return FundamentalMetrics(
            symbol=symbol,
            values=values,
            source=f"openbb:{self._provider}",
            collected_at=collected_at,
        )

    def get_macro_series(self, series: str) -> MacroObservation:
        series = series.strip().upper()
        if not series:
            raise ValueError("series must not be blank")

        response = self._client.economy.fred_series(
            symbol=series,
            provider=self._provider,
        )
        rows = tuple(_rows(response))
        if not rows:
            raise ValueError(f"OpenBB returned no observations for {series}")
        observations = tuple(
            (_as_utc(row["date"]), Decimal(str(row[series])))
            for row in rows
            if row.get(series) is not None
        )
        collected_at = self._clock()
        _require_aware_utc(collected_at, "clock result")
        return MacroObservation(
            series=series,
            observations=observations,
            source=f"openbb:{self._provider}",
            collected_at=collected_at,
        )

    def get_ohlcv_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> tuple[PriceBar, ...]:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be blank")
        _require_aware_utc(start, "start")
        _require_aware_utc(end, "end")
        if start >= end:
            raise ValueError("start must be earlier than end")

        response = self._client.equity.price.historical(
            symbol=symbol,
            start_date=start.date().isoformat(),
            end_date=end.date().isoformat(),
            provider=self._provider,
            interval=interval,
        )
        rows = _rows(response)
        collected_at = self._clock()
        _require_aware_utc(collected_at, "clock result")
        return tuple(
            PriceBar(
                symbol=symbol,
                interval=interval,
                timestamp=_as_utc(row["date"]),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
                source=f"openbb:{self._provider}",
                collected_at=collected_at,
                reference_date=_as_utc(row["date"]),
            )
            for row in rows
        )


def _load_openbb_client() -> Any:
    try:
        from openbb import obb
    except ImportError as error:
        raise RuntimeError(
            "OpenBB is not installed; install the project's OpenBB extra to use OpenBBProvider"
        ) from error
    return obb


def _rows(response: Any) -> Iterable[Mapping[str, Any]]:
    dataframe = response.to_df()
    if hasattr(dataframe, "to_dict"):
        # OpenBB returns the historical date as the DataFrame index.
        if hasattr(dataframe, "columns") and "date" not in dataframe.columns:
            dataframe = dataframe.reset_index()
        return dataframe.to_dict("records")
    return dataframe


def _as_utc(value: Any) -> datetime:
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)
    elif not isinstance(value, datetime):
        to_pydatetime = getattr(value, "to_pydatetime", None)
        if to_pydatetime is None:
            raise TypeError("OpenBB response dates must be datetime values")
        value = to_pydatetime()
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_aware_utc(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
