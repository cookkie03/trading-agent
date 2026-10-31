# Modulo Broker

Stato: implementazione di sola lettura, 2026-10-31. Codice in [`src/trading_agent/brokers/`](../src/trading_agent/brokers/). Il modulo legge il conto; non decide investimenti e non invia ordini.

## Contratto e file

| File | Responsabilità |
|---|---|
| [`interface.py`](../src/trading_agent/brokers/interface.py) | `Broker`, un `Protocol` con tre operazioni di lettura |
| [`models.py`](../src/trading_agent/brokers/models.py) | Modelli immutabili del progetto e `BrokerError` |
| [`alpaca.py`](../src/trading_agent/brokers/alpaca.py) | Mapping Alpaca, costruzione del client paper e traduzione degli errori |

I chiamanti usano il contratto e i modelli del progetto; i tipi dell'SDK restano dentro l'adapter. `Broker` è un contratto strutturale: una futura implementazione o un fake può soddisfarlo senza ereditare da una classe base.

```python
class Broker(Protocol):
    def get_account(self) -> Account: ...
    def get_positions(self) -> tuple[Position, ...]: ...
    def get_orders(self, query: OrderQuery | None = None) -> tuple[Order, ...]: ...
```

Non sono disponibili metodi per inviare, cancellare, sostituire ordini o chiudere posizioni. Intent log, recovery, guardrail ed execution appartengono ai passi successivi.

## Connessione e utilizzo

Il percorso normale usa credenziali Alpaca paper e seleziona esplicitamente il relativo ambiente:

```python
from trading_agent.brokers.alpaca import AlpacaBroker
from trading_agent.brokers.interface import Broker
from trading_agent.brokers.models import OrderQuery

broker: Broker = AlpacaBroker.from_env()
account = broker.get_account()
positions = broker.get_positions()
aapl_orders = broker.get_orders(OrderQuery(status="all", symbols=("AAPL",), limit=50))
```

`from_env()` richiede `ALPACA_API_KEY` e `ALPACA_SECRET_KEY`. Variabili assenti o vuote producono `ValueError` prima di chiamare la rete. Non carica `.env` automaticamente. `ALPACA_TRADING_URL` è opzionale e predefinita a `https://paper-api.alpaca.markets/v2`; viene normalizzata per l'SDK, che aggiunge il proprio prefisso `/v2`. `AlpacaBroker.paper(api_key, secret_key)` permette di passare le credenziali direttamente e usa sempre `paper=True`, senza fallback al live.

`AlpacaBroker(client)` riceve un `TradingClient` già costruito: consente di sostituire il trasporto nei test. Chi usa direttamente il costruttore è responsabile della configurazione del client; il costruttore non verifica che sia paper. Tutti i metodi esposti rimangono di lettura. Il range supportato è `alpaca-py>=0.44,<0.45`, con 0.44.0 risolta in `uv.lock`.

## Dati restituiti

I modelli sono `dataclass(frozen=True)`; collezioni e gambe degli ordini sono tuple.

- `Account`: identificatore, stato, valuta, `cash`, `equity`, `buying_power`, `trading_blocked`. La liquidità è distinta dal potere d'acquisto, che può includere margine. `trading_blocked=False` da solo non attesta l'autorizzazione o la possibilità di fare trading.
- `Position`: strumento, asset class, lato, quantità totale e disponibile, prezzo medio di ingresso, prezzo corrente, valore e P/L non realizzato. Gli importi possono essere assenti dove Alpaca non fornisce un valore; gli short conservano lato e quantità restituiti dal broker.
- `Order`: identificatori broker e cliente, strumento e asset class quando disponibili, lato, tipo, stato, quantità o notional, quantità eseguita, prezzi, timestamp e gambe annidate.

Importi e quantità sono `Decimal`; l'adapter rifiuta valori numerici non finiti. I timestamp degli ordini sono normalizzati a UTC; le informazioni non disponibili restano `None`. I valori vendor di stato, lato e asset class vengono conservati come stringhe, evitando di ridurli a un elenco incompleto di stati del progetto.

Lo scope strategico è azionario USA/USD, ma l'adapter non elimina posizioni o ordini di altre asset class presenti nel conto. Una vista completa delle esposizioni serve al monitoraggio; le regole di ammissibilità al trading verranno applicate dall'execution.

## Filtri degli ordini

`get_orders()` senza parametri equivale a `OrderQuery()`:

| Campo | Default e vincoli |
|---|---|
| `status` | `"open"`; ammessi anche `"closed"` e `"all"` |
| `symbols` | `()` significa nessun filtro; richiede una tupla di simboli non vuoti e senza spazi ai margini |
| `limit` | 100; intero da 1 a 500, esclusi booleani |
| `after`, `until` | Opzionali, con timezone; estremi esclusivi; se entrambi presenti, `after` precede `until` |

Gli ordini sono richiesti dal più recente al meno recente, con `nested=True` per conservare le gambe. La risposta è una finestra limitata: non c'è paginazione automatica e non rappresenta necessariamente lo storico completo. Un risultato di lunghezza pari al limite non dimostra che non esistano altri ordini.

## Errori e limiti operativi

Un errore di lettura non viene trasformato in un conto o elenco vuoto. L'adapter restituisce `BrokerError`, con `kind`, eventuale `status_code` HTTP ed eventuale `broker_code`:

| `kind` | Significato |
|---|---|
| `authentication` | HTTP 401/403 |
| `rate_limit` | HTTP 429 |
| `invalid_request` | Altri errori HTTP 4xx |
| `unavailable` | Errori di trasporto o risposta HTTP non classificata nelle categorie precedenti |
| `invalid_response` | JSON non valido anche con HTTP 200, campi richiesti mancanti, importi o timestamp non validi, risposta non mappabile |

Le factory `paper()` e `from_env()` montano un `HTTPAdapter` con timeout di connessione di 5 secondi e lettura di 30 secondi per richiesta. Il client passato direttamente al costruttore rimane configurato dal chiamante. L'SDK può ritentare alcune letture secondo la propria policy: questi timeout non sono una deadline totale, e il modulo non aggiunge una seconda policy di retry.

Alpaca SDK 0.44 non espone un parametro pubblico per questo timeout: il montaggio dell'adapter usa `client._session`, un dettaglio privato confinato in `alpaca.py`. Questa piccola dipendenza dall'implementazione dell'SDK richiede di rieseguire il test di regressione sul timeout a ogni upgrade del client.

Le tre letture sono richieste distinte, non una fotografia atomica del conto. Questo slice non offre streaming, riconciliazione periodica o storico persistente.

## Test e verifiche

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Verifica del 2026-10-31: **25 test offline passati e 1 test di integrazione saltato**. La suite offline attraversa il contratto con il vero SDK e HTTP simulato: controlla mapping, importi, filtri, gambe e timestamp, configurazione paper ed errori. Le regressioni su JSON invalido con HTTP 200 e timeout delle factory sono state verificate passando prima dal test fallito alla correzione funzionante (RED → GREEN). Non richiede chiavi. `mypy` verifica il package broker in modalità strict.

La prova sul servizio paper è separata ed esplicita. Copiare `.env.example` dalla radice in `.env` e compilare le due chiavi paper soltanto sul computer locale; non inviarle in chat. Il file `.env` è escluso da Git. Poi eseguire:

```bash
uv run --env-file .env pytest --alpaca-paper tests/integration -q
```

Senza `--alpaca-paper` il test d'integrazione viene saltato. Con il flag, l'assenza delle credenziali provoca un errore. Il test legge soltanto e non effettua ordini. Nessuna prova su conto Alpaca è stata eseguita in questa sessione: le credenziali non erano disponibili. Gli esempi con connessione non sono pertanto verificati sul servizio.

Per limiti della simulazione, API e vincoli dei futuri ordini vedere la [ricerca ufficiale Alpaca](research/alpaca-broker.md). Il comportamento implementato è distinto dal piano più ampio della [wiki execution](../../trading-agent-wiki/wiki/system/execution/execution.md).
