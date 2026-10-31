"""Adapter Alpaca di sola lettura; l'SDK rimane confinato in questo file."""

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, TypeVar, cast

from alpaca.common.enums import Sort
from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.models import Order as AlpacaOrder
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.models import TradeAccount
from alpaca.trading.requests import GetOrdersRequest
from requests import Response
from requests.adapters import HTTPAdapter
from requests.exceptions import JSONDecodeError, RequestException

from .models import Account, BrokerError, ErrorKind, Order, OrderQuery, Position

PAPER_TRADING_URL = "https://paper-api.alpaca.markets/v2"


def _sdk_base_url(trading_url: str) -> str:
    return trading_url.rstrip("/").removesuffix("/v2")


class AlpacaBroker:
    """Riceve il client per poter sostituire il trasporto nei test.

    Le factory paper/from_env puntano sempre al conto paper. Nessun metodo scrive
    sul conto. Il client iniettato esplicitamente rimane responsabilità del chiamante.
    """

    def __init__(self, client: TradingClient) -> None:
        self._client = client

    @classmethod
    def paper(
        cls,
        api_key: str,
        secret_key: str,
        trading_url: str = PAPER_TRADING_URL,
    ) -> "AlpacaBroker":
        """Crea un client paper, senza fallback al live."""
        if not api_key.strip() or not secret_key.strip():
            raise ValueError("Both Alpaca paper credentials are required")
        if not trading_url.strip():
            raise ValueError("Alpaca trading URL is required")
        client = TradingClient(
            api_key,
            secret_key,
            paper=True,
            url_override=_sdk_base_url(trading_url),
        )
        # alpaca-py 0.44 non espone un timeout: il coupling privato resta qui.
        client._session.mount("https://", _ReadTimeoutAdapter())
        return cls(client)

    @classmethod
    def from_env(cls) -> "AlpacaBroker":
        """Legge ALPACA_API_KEY e ALPACA_SECRET_KEY dall'ambiente, senza stamparle."""
        for name in ("ALPACA_API_KEY", "ALPACA_SECRET_KEY"):
            if not os.environ.get(name, "").strip():
                raise ValueError(f"Missing paper credential: {name}")
        trading_url = os.environ.get("ALPACA_TRADING_URL", PAPER_TRADING_URL)
        return cls.paper(
            os.environ["ALPACA_API_KEY"],
            os.environ["ALPACA_SECRET_KEY"],
            trading_url,
        )

    def get_account(self) -> Account:
        with _translate_errors():
            account = cast(TradeAccount, self._client.get_account())
            return Account(
                id=str(account.id),
                status=account.status.value,
                currency=_required(account.currency),
                cash=_decimal(account.cash),
                equity=_decimal(account.equity),
                buying_power=_decimal(account.buying_power),
                trading_blocked=_required(account.trading_blocked),
            )

    def get_positions(self) -> tuple[Position, ...]:
        with _translate_errors():
            positions = cast(list[AlpacaPosition], self._client.get_all_positions())
            return tuple(
                Position(
                    symbol=p.symbol,
                    asset_class=p.asset_class.value,
                    side=p.side.value,
                    quantity=_decimal(p.qty),
                    quantity_available=_optional_decimal(p.qty_available),
                    average_entry_price=_decimal(p.avg_entry_price),
                    current_price=_optional_decimal(p.current_price),
                    market_value=_optional_decimal(p.market_value),
                    unrealized_profit_loss=_optional_decimal(p.unrealized_pl),
                )
                for p in positions
            )

    def get_orders(self, query: OrderQuery | None = None) -> tuple[Order, ...]:
        """Finestra limitata, ordinata per invio decrescente; gambe sempre annidate."""
        query = query or OrderQuery()
        request = GetOrdersRequest(
            status=QueryOrderStatus(query.status),
            limit=query.limit,
            symbols=list(query.symbols) or None,
            after=query.after,
            until=query.until,
            nested=True,
            direction=Sort.DESC,
        )
        with _translate_errors():
            orders = cast(list[AlpacaOrder], self._client.get_orders(filter=request))
            return tuple(_order(order) for order in orders)


class _ReadTimeoutAdapter(HTTPAdapter):
    """Timeout di connessione/lettura per richiesta, non deadline del ciclo intero."""

    def send(self, *args: Any, **kwargs: Any) -> Response:
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = (5.0, 30.0)
        return super().send(*args, **kwargs)


def _order(order: AlpacaOrder) -> Order:
    return Order(
        id=str(order.id),
        client_order_id=order.client_order_id,
        symbol=order.symbol,
        asset_class=order.asset_class.value if order.asset_class else None,
        side=order.side.value if order.side else None,
        order_type=order.type.value if order.type else None,
        status=order.status.value,
        quantity=_optional_decimal(order.qty),
        notional=_optional_decimal(order.notional),
        filled_quantity=_decimal(order.filled_qty),
        limit_price=_optional_decimal(order.limit_price),
        stop_price=_optional_decimal(order.stop_price),
        average_fill_price=_optional_decimal(order.filled_avg_price),
        submitted_at=_utc(order.submitted_at),
        filled_at=_utc(order.filled_at),
        legs=tuple(_order(leg) for leg in order.legs or ()),
    )


T = TypeVar("T")


def _required(value: T | None) -> T:
    if value is None:
        raise ValueError("Missing required broker field")
    return value


def _decimal(value: str | float | None) -> Decimal:
    result = Decimal(str(_required(value)))
    if not result.is_finite():
        raise ValueError("Non-finite broker amount")
    return result


def _optional_decimal(value: str | float | None) -> Decimal | None:
    return None if value is None else _decimal(value)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Broker timestamp has no timezone")
    return value.astimezone(UTC)


@contextmanager
def _translate_errors() -> Iterator[None]:
    try:
        yield
    except APIError as exc:
        status = cast(int | None, exc.status_code)
        kind: ErrorKind = "unavailable"
        if status in (401, 403):
            kind = "authentication"
        elif status == 429:
            kind = "rate_limit"
        elif status is not None and 400 <= status < 500:
            kind = "invalid_request"
        code = None
        try:
            body = json.loads(str(exc))
            if isinstance(body, dict) and body.get("code") is not None:
                code = str(body["code"])
        except (ValueError, TypeError):
            pass
        raise BrokerError(kind, status_code=status, broker_code=code) from exc
    except JSONDecodeError as exc:
        raise BrokerError("invalid_response") from exc
    except RequestException as exc:
        raise BrokerError("unavailable") from exc
    except (ValueError, TypeError, AttributeError, ArithmeticError) as exc:
        raise BrokerError("invalid_response") from exc
