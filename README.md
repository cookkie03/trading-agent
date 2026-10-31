# Trading Agent

Progetto Python per un sistema multi-agente di analisi e gestione di un portafoglio azionario. Gli agenti elaborano informazioni e proposte; calcoli, controlli di rischio ed esecuzione restano deterministici.

## Stato attuale

**2026-10-31 — primo modulo Broker di sola lettura.** La struttura modulare è approvata; sono presenti il contratto `Broker`, i modelli indipendenti dal vendor e l'adapter `AlpacaBroker` per leggere conto, posizioni e ordini. Il contratto non espone operazioni di invio, modifica o cancellazione degli ordini. Non esiste ancora un runtime autonomo di trading.

Il commit locale `88ca413` ha rimosso l'implementazione precedente conservando le skill di Matt Pocock e le istruzioni del progetto. Il codice storico è [consultabile nella cronologia](https://github.com/cookkie03/trading-agent/tree/20bf209).

Il layer dati espone `MarketDataProvider` e `PriceBar`, indipendenti dal vendor. Sono disponibili due adapter sostituibili: `YahooFinanceProvider` diretto e `OpenBBProvider`. OpenBB è opzionale e viene installato con `uv sync --extra openbb`; l'adapter conserva il provider sottostante nella provenance (`openbb:yfinance`) e non espone tipi OpenBB al resto dell'applicazione. OpenBB resta quindi un percorso di raccolta dati, non il contratto del progetto.

## Setup e verifiche locali

Prerequisiti: Python 3.11+ e `uv`. Le dipendenze runtime e sviluppo sono bloccate in `uv.lock`; il range supportato è `alpaca-py>=0.44,<0.45`, con versione 0.44.0 nel lock.

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Verifica del 2026-10-31: **25 test offline passati e 1 test di integrazione saltato**. La suite predefinita usa il vero SDK Alpaca con risposte HTTP simulate, senza chiavi né accesso a un conto. La verifica di tipizzazione è attualmente limitata al package `brokers`. Le prove di integrazione paper sono opt-in e richiedono credenziali; non è stata eseguita alcuna prova su un conto Alpaca in questa sessione.

## Prima lettura del conto paper

Impostare `ALPACA_API_KEY` e `ALPACA_SECRET_KEY` nell'ambiente con credenziali paper. `from_env()` legge queste variabili; il codice non carica automaticamente un file `.env`.

```python
from trading_agent.brokers.alpaca import AlpacaBroker
from trading_agent.brokers.interface import Broker

broker: Broker = AlpacaBroker.from_env()
account = broker.get_account()
positions = broker.get_positions()
open_orders = broker.get_orders()
```

Le factory `paper()` e `from_env()` selezionano sempre Alpaca paper. Questo esempio accede alla rete e richiede un conto; non è stato eseguito qui. Per modelli, filtri, errori e limiti vedere [il modulo Broker](docs/brokers.md).

## Architettura e ambito

La wiki definisce un **monolite modulare**, con broker e fonti dati sostituibili, database come hub persistente e separazione tra calcoli, strumenti, agenti e orchestrazione. Python è il linguaggio scelto; LangGraph e LangSmith sono le scelte documentate per il futuro layer agentico e non dipendenze del modulo attuale.

Il primo adapter dati è `YahooFinanceProvider`: legge OHLCV storico tramite yfinance e lo normalizza in `PriceBar`. Gli agenti non chiamano Yahoo Finance direttamente; per capacità e limiti vedere [la ricerca Yahoo Finance](docs/research/yahoo-finance.md).

L'MVP è **paper trading su azioni USA in USD**. La lettura del conto conserva eventuali posizioni e ordini di altri asset già presenti, così da non nascondere esposizioni. Questo non autorizza operazioni fuori ambito. La struttura `src/trading_agent/` è presente; il primo modulo funzionale è `brokers`, mentre gli altri package mantengono il ruolo di scaffolding.

## Documentazione e sviluppo

| Documento | Cosa contiene |
|---|---|
| [Trading Agent Wiki](https://github.com/cookkie03/trading-agent-wiki) | Requisiti, decisioni, backlog e fonti condivise |
| [Architettura](docs/architecture.md) | Organizzazione del codice, dipendenze e passi successivi |
| [Modulo Broker](docs/brokers.md) | Contratto implementato, esempi, test e limiti |
| [Ricerca Alpaca](docs/research/alpaca-broker.md) | Fatti tecnici dalle fonti ufficiali e limiti della simulazione |
| [Manutenzione della documentazione](docs/documentation.md) | Quali documenti aggiornare e come verificarli |
| [AGENTS.md](AGENTS.md) | Regole operative per gli agenti che lavorano nel progetto |

Prima di ogni lavoro consultare la [overview della wiki](../trading-agent-wiki/wiki/overview.md) e le pagine pertinenti. Per i link locali clonare le due repository nella stessa cartella padre, con nomi `trading-agent` e `trading-agent-wiki`.

Si procede per step: wiki → confronto sui contratti → test del comportamento → implementazione → verifica e aggiornamento documentazione. Si usano le skill pertinenti di Matt Pocock, in particolare `codebase-design`, `domain-modeling`, `tdd` e `code-review`.

## Integrazione Alpaca paper

Copiare `.env.example` in `.env` e inserire localmente le credenziali paper, senza inviarle in chat. `.env` è escluso da Git. Eseguire esplicitamente il test di sola lettura:

```bash
uv run --env-file .env pytest --alpaca-paper tests/integration -q
```

Senza il flag il test di rete viene saltato; con il flag e credenziali mancanti fallisce. Non vengono inviati ordini. Il paper trading è una simulazione e non dimostra il comportamento di esecuzione sul mercato reale.

## Docker

Il deploy in produzione tramite Docker è un requisito confermato. È presente `.dockerignore`; Dockerfile e avvio container saranno definiti quando esisterà un flusso applicativo eseguibile. Il modulo attuale è una libreria di lettura: nessuna immagine Docker è stata costruita o distribuita.
