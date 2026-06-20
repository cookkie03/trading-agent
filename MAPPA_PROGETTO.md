# 🗺️ Mappa del Progetto & Guida alla Lettura del Codice

Benvenuto nella mappa dettagliata di **trading-agent**, un fondo di investimento AI autonomo e multi-agente. Questa guida ti aiuterà a orientarti all'interno della codebase, a comprendere come interpretare ciascun file e a tracciare i flussi di esecuzione che connettono le varie componenti.

---

## 📂 Struttura del Progetto (Albero della Directory)

```text
trading-agent/
├── .tradingagents/                 # 💾 Cartella locale per database SQLite, logs e PID (creata all'avvio)
├── config.toml                     # File di configurazione globale (parametri quantitativi, LLM, broker)
├── docker-compose.yml              # Configurazione per containerizzare il database e la dashboard
├── Dockerfile                      # Ricetta Docker per il deployment del sistema
├── nginx-tradingagents.conf        # Configurazione reverse-proxy per esporre la dashboard/log
├── pyproject.toml / uv.lock        # Gestione delle dipendenze del progetto (tramite uv)
├── test.py                         # Script rapido di test manuale
│
├── scripts/                        # Script di utilità e sviluppo
│   ├── run_dashboard.py            # Avvio del server streamlit della dashboard
│   ├── smoke_structured_output.py  # Smoke test per verificare gli output strutturati dei modelli LLM
│   └── trading-agent-dashboard.service # File di servizio systemd per Linux
│
├── tests/                          # Suite di test offline e di integrazione (216+ test)
│   ├── conftest.py                 # Fixture condivise e mock del database/LLM per i test
│   └── test_*.py                   # Test unitari per ciascun modulo
│
├── reports/                        # Report generati autonomamente dagli agenti (es. MONC.MI, NVDA)
│   └── <ticker>_<timestamp>/       # Cartelle con analisi dei desk, PM, Risk e report finale
│
└── tradingagents/                  # 💻 Il Package Principale del Codice
    ├── __init__.py                 # Inizializzazione package
    ├── app.py                      # Punto di ingresso per i cicli singoli (run_once) e infiniti (run_forever)
    ├── cli.py                      # Interfaccia a riga di comando (CLI) per controllare il sistema
    ├── config.py                   # Gestione della configurazione (legge config.toml e .env)
    ├── daemon.py                   # Gestore del processo demone in background (start/stop/status)
    ├── default_config.py           # Valori di default per i parametri di configurazione
    ├── performance.py              # Calcoli statistici di portafoglio (Sharpe, Calmar, Alpha, Beta)
    ├── benchmark.py                # Gestione dell'ingestione e confronto con il benchmark (es. SPY)
    │
    ├── backtesting/                # 🧪 Motore di Backtesting Deterministico
    │   ├── __init__.py
    │   ├── engine.py               # Simulatore ATR long-only con walk-forward e sweep dei parametri
    │   ├── engine_vbt.py           # Backtesting vettorializzato opzionale tramite VectorBT
    │   └── scheduler.py            # Job notturno che calcola i parametri ottimali per ciascun ticker
    │
    ├── brain/                      # 🧠 Il "Cervello" AI (Multi-Agent System)
    │   ├── __init__.py
    │   ├── agent_context.py        # Rappresentazione dello stato e del contesto specifico di ogni agente
    │   ├── context.py              # Funzioni per compilare i dati DB in stringhe leggibili dagli agenti
    │   ├── datapizza_director.py   # Gestore parallelo (ThreadPool) per analizzare più ticker contemporaneamente
    │   ├── datapizza_graph.py      # Definizione del grafo degli agenti (Market, Sentiment, Tech, Fund -> PM -> Risk)
    │   ├── datapizza_llm.py        # Client unificato per LLM (OpenAI, Anthropic, Gemini, DeepSeek) con output strutturato
    │   ├── datapizza_tools.py      # I tool ("Extractors") che gli agenti possono invocare per interrogare il DB
    │   ├── prompts.py              # System prompt per ciascun agente (istruzioni di analisi, bias da evitare)
    │   ├── schemas.py              # Schemi Pydantic per validare le risposte strutturate degli agenti
    │   └── warmup.py               # Esegue gli estrattori per pre-popolare il DB prima che gli agenti leggano il contesto
    │
    ├── broker/                     # 🔌 Adattatori Broker (Simulati e Reali)
    │   ├── __init__.py
    │   ├── base.py                 # Classe astratta Broker che definisce l'interfaccia comune
    │   ├── commission.py           # Modelli di commissione simulati (fissi, percentuali, gratuiti)
    │   ├── paper.py                # Broker simulato in-memory per test e simulazioni offline
    │   ├── alpaca.py               # Adattatore reale/paper per la piattaforma Alpaca API
    │   └── ibkr.py                 # Adattatore reale/paper per Interactive Brokers (TWS / IB Gateway)
    │
    ├── dashboard/                  # 📊 Dashboard Streamlit per Osservabilità (Read-Only)
    │   ├── app.py                  # Entrypoint Streamlit (visualizzazione portafoglio, log e decisioni)
    │   ├── db_reader.py            # Estrattore di dati dal DB specifico per la dashboard
    │   ├── metrics.py              # Calcolo delle metriche visive (NAV, profit/loss giornalieri, drawdown)
    │   ├── components/             # Componenti UI (sidebar, pannello metriche)
    │   └── views/                  # Viste e sotto-pagine (panoramica, transazioni, watchlist, analisi ticker)
    │
    ├── data/                       # 🗃️ Dati statici e seed
    │   └── sp500.csv               # File CSV usato per popolare l'universo iniziale di ticker
    │
    ├── dataflows/                  # 📡 Integrazione con Vendor di Dati (API ed Estrattori)
    │   ├── __init__.py
    │   ├── interface.py            # Interfaccia base dei Fetcher di dati
    │   ├── utils.py                # Utilità di rete (retry, backoff esponenziale)
    │   ├── alpha_vantage_*.py      # Estrattori Alpha Vantage (Fundamentals, News, Technicals, Prices)
    │   ├── y_finance.py            # Estrattore per prezzi storici e real-time via Yahoo Finance
    │   ├── yfinance_news.py        # Ingestore di notizie da Yahoo Finance
    │   ├── reddit.py               # Estrattore di post e commenti da subreddit finanziari
    │   ├── stocktwits.py           # Estrattore del flusso social da StockTwits
    │   ├── stockstats_utils.py     # Helper per calcolare indicatori tecnici partendo da DataFrame grezzi
    │   └── config.py               # Isolamento della configurazione dei dataflow
    │
    ├── domain/                     # 🛡️ Logica di Dominio e Modelli Matematici Deterministici
    │   ├── __init__.py
    │   ├── enums.py                # Enumerazioni core (Direzioni di trading, Verdicts del Risk Analyst)
    │   ├── state.py                # Modello `ResearchState` (il documento che sigilla l'intera tesi di investimento)
    │   └── risk.py                 # Motore di rischio numerico (ATR stop/target, position sizing, Statute)
    │
    ├── execution/                  # ⚡ Gestione degli Ordini e della Posizione
    │   ├── __init__.py
    │   ├── costs.py                # Controllo Net-EV (verifica se il profitto atteso copre commissioni e costi LLM)
    │   ├── disinvest.py            # Liquidazione automatica delle posizioni più deboli per liberare capitale
    │   ├── exits.py                # Gestione automatica delle uscite (Take Profit / Stop Loss hit)
    │   ├── helpers.py              # Funzioni di utilità per l'esecuzione degli ordini
    │   ├── submit.py               # Persiste e prepara la transazione a database
    │   ├── trade.py                # Invia l'ordine al broker e gestisce le risposte (idempotente)
    │   └── mantainer.py            # Sincronizza lo stato del portafoglio sul DB con quello reale del broker
    │
    ├── indicators/                 # 📈 Calcolo degli Indicatori Tecnici
    │   ├── __init__.py
    │   ├── core.py                 # Formule matematiche pure (ATR, EMA, 52-week High/Low)
    │   └── db.py                   # Legge i dati storici sul DB e vi applica le formule di `core.py`
    │
    ├── ingestion/                  # 📥 Pipeline di Ingestione nel Database (DB-First)
    │   ├── __init__.py
    │   ├── price_ingest.py         # Scarica e scrive i prezzi OHLCV sul DB (double-dated per evitare look-ahead bias)
    │   ├── fundamentals_ingest.py  # Salva le metriche fondamentali sul DB
    │   ├── news_ingest.py          # Salva e de-duplica le notizie
    │   ├── social_ingest.py        # Salva i commenti dei social media
    │   ├── macro_ingest.py         # Salva i dati macroeconomici globali (es. tassi di interesse, CPI)
    │   └── screening.py            # Esegue lo screening tecnico di base per taggare i ticker promettenti
    │
    ├── orchestration/              # 🔄 Schedulatore e Motore dei Cicli
    │   ├── __init__.py
    │   ├── cycle.py                # Esegue le fasi del ciclo (Exits -> Triggers -> Brain -> Risk Gate -> Execution)
    │   ├── datapizza_analyze.py    # Interfaccia che connette la pipeline degli agenti con il ciclo di esecuzione
    │   └── triggers.py             # Rileva gli eventi e popola la coda dei ticker da analizzare con priorità
    │
    ├── storage/                    # 💾 Livello di Persistenza (Database SQL)
    │   ├── __init__.py
    │   ├── database.py             # Setup della connessione SQLAlchemy e gestione delle transazioni
    │   ├── models/                 # Definizione delle tabelle SQLAlchemy
    │   │   ├── __init__.py
    │   │   ├── backtest.py         # Storico dei risultati di backtesting
    │   │   ├── charter.py          # Parametri dello Statuto interno del fondo
    │   │   ├── instrument.py       # Ticker dell'universo e informazioni di settore
    │   │   ├── market.py           # Prezzi storici, notizie e macroeconomia
    │   │   ├── portfolio.py        # Storico NAV e snapshot delle posizioni aperte
    │   │   ├── research.py         # Stato finale di ricerca e tesi salvate (ResearchState)
    │   │   └── trade.py            # Storico degli ordini eseguiti
    │   └── repository/             # Classi Repository per isolare le query SQL dal codice applicativo
    │
    ├── tools/                      # 🛠️ Definizione dei Tool per gli Agenti
    │   ├── __init__.py
    │   ├── market.py               # Tool per interrogare prezzi di mercato e dati macro
    │   ├── options.py              # Tool per analizzare le catene di opzioni (opzionale)
    │   └── portfolio.py            # Tool per verificare la liquidità e i rischi del portafoglio corrente
    │
    └── universe/                   # 🌌 Universo dei Titoli Tradabili
        ├── __init__.py
        ├── sources.py              # Legge l'universo iniziale dal CSV
        └── sync.py                 # Sincronizza l'universo incrociando i dati con i ticker offerti dal broker
```

---

## 🔄 Tracciamento del Processo: Come Funziona un Ciclo Autonomo?

Per comprendere appieno come interagiscono i file, seguiamo il flusso logico di un singolo ciclo di esecuzione (il battito cardiaco del sistema), orchestrato in [tradingagents/orchestration/cycle.py](file:///Users/luca/Desktop/trading-agent/tradingagents/orchestration/cycle.py).

### Fase 1: Chiusura delle Posizioni Aperte (Exits)
Prima di fare qualsiasi nuova analisi, il sistema controlla se ci sono posizioni che hanno raggiunto i propri limiti.
1. `run_cycle()` chiama `manage_exits()` situato in [execution/exits.py](file:///Users/luca/Desktop/trading-agent/tradingagents/execution/exits.py).
2. Questo legge i prezzi storici correnti e controlla se il prezzo attuale ha toccato il **Take Profit** o lo **Stop Loss** fissati a database nella tabella `trades`.
3. Se un target viene colpito, viene inviato un ordine di vendita al broker (`broker/`) per chiudere la posizione.

### Fase 2: Raccolta dei Trigger (Cosa analizzare oggi?)
Il sistema decide quali titoli meritano attenzione in questo ciclo.
1. Viene chiamato `collect_triggers()` in [orchestration/triggers.py](file:///Users/luca/Desktop/trading-agent/tradingagents/orchestration/triggers.py).
2. Vengono controllate:
   - Date di scadenza delle analisi passate (`next_check_date` sul DB).
   - Eventi sul calendario (es. report trimestrali).
   - Alert di prezzo o anomalie di volume.
3. Se un evento accade su un titolo non ancora nella nostra watchlist, ma presente nell'universo complessivo, viene inserito dinamicamente nella watchlist (`_admit_watchlist`).

### Fase 3: Il Processo Decisionale Multi-Agente (The Brain)
Per ciascun titolo candidato ad essere scambiato, viene avviata l'analisi cognitiva. Il punto di ingresso è `analyze_symbol()` in [brain/datapizza_graph.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/datapizza_graph.py).

1. **Warm Start (`brain/warmup.py`)**: Prima che gli agenti leggano i contesti, gli estrattori automatici scaricano le metriche correnti (prezzi storici, ultime notizie, bilanci) in modo che i tool chiamati successivamente abbiano già dati freschi a database.
2. **I Desk Analisti (Sequenziali)**:
   Vengono lanciati 4 agenti specialisti (`datapizza.agents.Agent`) configurati con i prompt definiti in [brain/prompts.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/prompts.py). Ciascuno usa i propri tool definiti in [brain/datapizza_tools.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/datapizza_tools.py):
   - **Market Desk**: Analizza l'andamento macroeconomico e i prezzi del mercato.
   - **Sentiment Desk**: Valuta la reazione dei social media e del sentiment delle news.
   - **Technical Desk**: Legge indicatori tecnici come EMA e ATR calcolati da [indicators/db.py](file:///Users/luca/Desktop/trading-agent/tradingagents/indicators/db.py).
   - **Fundamental Desk**: Legge i bilanci storici, flussi di cassa e margini di crescita.
   *Ciascun Desk produce una risposta strutturata sul modello `DeskOpinion` ([brain/schemas.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/schemas.py)).*
3. **Portfolio Manager (PM)**:
   L'agente PM riceve le 4 opinioni dei desk ed esegue una sintesi.
   - Produce un giudizio (`PMDecision`): Direzione (`STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL`), Conviction, Pro e Contro.
   - Fornisce i parametri ATR desiderati per il trade (`k_entry`, `k_stop`, `k_tp`).
   - Calcola i livelli reali di prezzo (prezzo d'entrata, stop loss, take profit) invocando la formula deterministica `atr_levels()` in [domain/risk.py](file:///Users/luca/Desktop/trading-agent/tradingagents/domain/risk.py).
4. **Risk Analyst Gate**:
   L'ultimo agente, il Risk Analyst, analizza la tesi proposta dal PM.
   - Calcola il dimensionamento corretto della posizione (`position_size()` in [domain/risk.py](file:///Users/luca/Desktop/trading-agent/tradingagents/domain/risk.py)) basandosi sulla volatilità (ATR) e la frazione di rischio del portafoglio (portfolio heat).
   - Esegue i controlli dello **Statuto** (`check_guardrails()`):
     - Rischio/Rendimento minimo (es. >= 1.5).
     - Esposizione massima per singolo titolo (es. <= 10%).
     - Riserva strategica di cassa (mantenere almeno il 10% in liquidità).
     - Limite di concentrazione per settore economico (es. <= 30%).
   - Se uno qualsiasi dei controlli numerici dello Statuto fallisce, l'ordine viene **automaticamente rifiutato** (`SEND_BACK`) e rimandato indietro per la revisione degli agenti.
   - Se lo Statuto passa, il Risk Analyst decide se approvare la tesi (`APPROVED`).

### Fase 4: Validazione Finale ed Esecuzione
Una volta ottenute le tesi approvate, il ciclo torna nella parte interamente deterministica in [orchestration/cycle.py](file:///Users/luca/Desktop/trading-agent/tradingagents/orchestration/cycle.py).

1. **Cost Gate (`execution/costs.py`)**: Viene controllato se il trade stimato ha un rendimento atteso al netto dei costi (Expected Value netta) sufficiente a coprire sia le commissioni del broker che il costo dei token LLM utilizzati per generare l'analisi.
2. **Statuto del Portafoglio (`execution/portfolio_risk.py` / `admit_within_statute`)**: Anche se un singolo titolo è legale da solo, il gestore di portafoglio controlla se l'insieme di tutti i nuovi acquisti previsti per questo ciclo viola i limiti complessivi (es. se compriamo 3 titoli tecnologici insieme superiamo il tetto massimo del 30% per il settore Tech?). Solo i trade ammessi superano questo cancello.
3. **Persistenza & Invio (`execution/trade.py` & `execution/submit.py`)**:
   L'ordine approvato viene registrato come `pending` sul DB SQL per evitare doppie esecuzioni. Successivamente l'adattatore del broker corrente (`broker/alpaca.py` o `broker/ibkr.py`) esegue la transazione a mercato.
4. **Sincronizzazione (Mantainer)**: Viene lanciato `run_mantainer()` ([execution/mantainer.py](file:///Users/luca/Desktop/trading-agent/tradingagents/execution/mantainer.py)) che scarica la rendicontazione aggiornata dal broker e salva un nuovo snapshot del portafoglio sul database, pronto per il ciclo successivo.
5. **Decision Log (`storage/repository/research.py`)**: La decisione completa di ciascun ticker viene archiviata sul DB come "Decision Log" per supportare l'apprendimento degli agenti e l'osservabilità futura.

---

## 🛠️ Come interpretare i file chiave per i tuoi scopi

Se vuoi comprendere il codice approfondendo punti specifici:

| Se vuoi capire... | File a cui fare riferimento | Descrizione veloce |
| :--- | :--- | :--- |
| **Come è fatto il database** | [storage/models.py](file:///Users/luca/Desktop/trading-agent/tradingagents/storage/models.py) | Mostra lo schema di tutte le tabelle (prezzi, transazioni, portafoglio, ricerche). |
| **Come gli agenti ragionano** | [brain/prompts.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/prompts.py) | Contiene le istruzioni esatte date ai modelli LLM per agire da esperti di mercato. |
| **Come si calcola la taglia dei trade** | [domain/risk.py](file:///Users/luca/Desktop/trading-agent/tradingagents/domain/risk.py) | È il cuore matematico: contiene le regole di stop/target e il calcolo del numero di azioni. |
| **Quali dati leggono gli agenti** | [brain/context.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/context.py) | Gestisce l'estrazione e formattazione dei dati dal database per iniettarli nella finestra di contesto dell'agente. |
| **Come testare offline** | [tests/conftest.py](file:///Users/luca/Desktop/trading-agent/tests/conftest.py) | Configura l'ambiente simulato (`_FakeLLM` e `FakeFetcher`) usato per far girare i test offline senza sprecare chiavi API. |
| **Come visualizzare i dati storici** | [dashboard/app.py](file:///Users/luca/Desktop/trading-agent/tradingagents/dashboard/app.py) | È il frontend in Streamlit che legge il DB e mostra l'attività del fondo. |

---

## 🚀 Passi Consigliati per Leggere il Codice

1. **Parti da [tradingagents/app.py](file:///Users/luca/Desktop/trading-agent/tradingagents/app.py)**: Guarda la funzione `run_once()` per capire la sequenza globale delle funzioni.
2. **Apri [tradingagents/orchestration/cycle.py](file:///Users/luca/Desktop/trading-agent/tradingagents/orchestration/cycle.py)**: Segui come sono strutturate le fasi del ciclo reale.
3. **Esplora il Grafo in [tradingagents/brain/datapizza_graph.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/datapizza_graph.py)**: Leggi `analyze_symbol()` per vedere come i 4 Desk collaborano per arrivare alla tesi di investimento.
4. **Analizza la logica quantitativa in [tradingagents/domain/risk.py](file:///Users/luca/Desktop/trading-agent/tradingagents/domain/risk.py)**: Studia come le decisioni qualitative dell'LLM sono ricondotte a prezzi numerici precisi.

---

## 🔧 Modifiche e Ottimizzazioni Recenti

Durante l'ultima fase di test e messa in produzione, sono state implementate diverse migliorie per garantire l'autocontenimento della repository, la stabilità e la leggibilità:

1. **Autocontenimento delle Risorse (`.tradingagents/`)**: 
   Tutta la persistenza locale (il database SQLite `trading_agent.db`, i log `agent.log`, i PID dei processi e le cache) è stata spostata nella cartella `.tradingagents/` posizionata nella root del progetto. In questo modo il software non genera alcun file o cartella al di fuori della repository. La cartella è stata inserita nel file [.gitignore](file:///Users/luca/Desktop/trading-agent/.gitignore).
2. **Dashboard Streamlit Riorganizzata (`dashboard/views`)**: 
   Per evitare che Streamlit caricasse automaticamente viste vuote nella sidebar nativa, le pagine individuali sono state spostate da `pages/` a `views/`. La navigazione è ora interamente gestita dal menu orizzontale e funzionale presente in [dashboard/app.py](file:///Users/luca/Desktop/trading-agent/tradingagents/dashboard/app.py).
3. **Restyling e Leggibilità Grafica**: 
   È stato applicato un tema scuro moderno ad alto contrasto (configurato in [.streamlit/config.toml](file:///Users/luca/Desktop/trading-agent/.streamlit/config.toml)) con colori indaco/ardesia e testi chiari nitidi, rendendo la dashboard perfettamente leggibile su qualsiasi schermo.
4. **Prevenzione Lock del Database SQLite**: 
   Le lunghe transazioni SQL del ciclo `run_once` in [app.py](file:///Users/luca/Desktop/trading-agent/tradingagents/app.py) sono state spezzate e committate su base per-symbol. Questo evita il blocco in scrittura esclusivo di SQLite e risolve gli errori di timeout (database is locked) che impedivano alla dashboard di leggere i dati in tempo reale.
5. **Esclusione NaN nell'Ingestione Prezzi**: 
   Il modulo [price_ingest.py](file:///Users/luca/Desktop/trading-agent/tradingagents/ingestion/price_ingest.py) ora esclude esplicitamente i dati incompleti/NaN ritornati da Yahoo Finance per evitare fallimenti di vincoli sul DB.
6. **Configurazione OpenRouter**: 
   È stato corretto il base URL e l'inizializzazione del client OpenRouter in [datapizza_llm.py](file:///Users/luca/Desktop/trading-agent/tradingagents/brain/datapizza_llm.py) per supportare correttamente le chiamate ai modelli di terze parti con output strutturato.

---

## 🚀 Esecuzione in Locale (senza Docker)

Il sistema è configurato per essere eseguito nativamente in ambiente locale usando `uv`.

### 1. Avvio del Demone di Trading e Backtest (Background)
Per lanciare il ciclo autonomo e il backtest notturno in background:
```bash
uv run python -m tradingagents.cli start
```
*I log di esecuzione verranno scritti in [.tradingagents/agent.log](file:///Users/luca/Desktop/trading-agent/.tradingagents/agent.log).*

### 2. Monitoraggio dello Stato
Per verificare se il sistema è attivo ed identificare i PID:
```bash
uv run python -c "import logging; logging.basicConfig(level=logging.INFO); import tradingagents.cli; tradingagents.cli.main(['status'])"
```

### 3. Avvio della Dashboard Streamlit
Per lanciare l'interfaccia di monitoraggio su [http://127.0.0.1:8501](http://127.0.0.1:8501):
```bash
uv run streamlit run tradingagents/dashboard/app.py --server.port=8501 --server.address=127.0.0.1
```

### 4. Arresto del Demone
Per arrestare tutti i processi in background in modo pulito:
```bash
uv run python -m tradingagents.cli stop
```

