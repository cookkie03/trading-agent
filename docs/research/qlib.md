---
title: "Microsoft Qlib — valutazione per il quantitative engine"
type: research
status: active
area: software
created: 2026-11-02
updated: 2026-11-02
---

# Microsoft Qlib — valutazione per il quantitative engine

**Stato del documento:** ricerca su fonti upstream ufficiali verificata il 2026-11-02. La raccomandazione è una proposta tecnica per il quantitative engine; non è una decisione chiusa né un'implementazione. Le versioni upstream e le dipendenze vanno riverificate prima dell'adozione.

## 1. Risposta breve

Qlib è un framework open-source di Microsoft per la ricerca quantitativa guidata da AI e il passaggio dalla ricerca alla produzione. Copre dati, feature engineering, dataset, modelli, workflow, backtest, portfolio analysis e serving. Il repository dichiara licenza MIT e l'ultima release GitHub ufficiale consultata è **v0.9.8**, non prerelease, pubblicata l'8 ottobre 2026. [Repository README](https://github.com/microsoft/qlib#readme-ov-file), [LICENSE](https://github.com/microsoft/qlib/blob/main/LICENSE), [release v0.9.8](https://github.com/microsoft/qlib/releases/tag/v0.9.8)

**Raccomandazione:** non adottare Qlib come data layer o contratto applicativo del trading-agent. Valutarlo come **motore opzionale dietro un modulo proprio di quantitative research**, riusando pattern e, solo dopo una prova d'integrazione, le parti necessarie per feature/dataset/model/backtest. Il provider seam, `PriceBar`, la provenance SQLite e gli state contract devono restare nostri.

## 2. Cosa offre upstream

### Data layer

Il data layer Qlib separa download/conversione dei dati, storage nativo, loader, `DataHandler` e `Dataset`. La documentazione descrive il percorso: dati raw convertiti nel formato `.bin`; expression engine e loader per costruire feature; processor dentro un data handler; dataset per preparare l'input del modello. [Data Layer](https://qlib.readthedocs.io/en/latest/component/data.html), [get data](https://qlib.readthedocs.io/en/latest/start/getdata.html), [repository `qlib/data`](https://github.com/microsoft/qlib/tree/main/qlib/data)

Sono documentate modalità offline locale e online tramite data server, caching, layout dei file, conversioni CSV/Parquet e health check. Il README segnala inoltre che il dataset pubblico di esempio è attualmente ottenuto da una fonte community perché il dataset ufficiale è temporaneamente disabilitato: questo è un costo operativo e non va confuso con una garanzia di disponibilità dati. [README, Data Preparation](https://github.com/microsoft/qlib#data-preparation), [README, Offline and Online Mode](https://github.com/microsoft/qlib#offline-mode-and-online-mode), [data docs](https://qlib.readthedocs.io/en/latest/component/data.html)

Il codice upstream di [`DataHandler`](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py) costruisce/fetch-a dati tabellari e supporta selezione di indici/colonne e finestre temporali. `DataHandlerLP` separa raw, inference e learning data e applica `shared_processors`, `infer_processors` e `learn_processors`; i processor possono essere fit-tati sui dati storici e riutilizzati sui nuovi dati. [DataHandlerLP docs](https://qlib.readthedocs.io/en/latest/component/data.html#data-handler)

Qlib ha anche una implementazione file-based di point-in-time (PIT) per fattori fondamentali annuali/trimestrali: conserva publication date, reporting period, valore e puntatori/index per la lookup storica. La documentazione dichiara che il calcolo PIT è funzionale ma non ancora ottimizzato per performance. [PIT docs](https://qlib.readthedocs.io/en/latest/advanced/PIT.html), [PIT implementation path](https://github.com/microsoft/qlib/tree/main/qlib/contrib/data/pit)

### Feature engineering

Le feature possono derivare dai campi provider come `$open`, `$high`, `$low`, `$close` e da operatori di espressione; la documentazione collega l'implementazione degli operatori a [`qlib/data/ops.py`](https://github.com/microsoft/qlib/blob/main/qlib/data/ops.py). Qlib offre handler predefiniti come `Alpha158` in [`qlib.contrib.data.handler`](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py), configurabili con intervalli, instruments, features, labels e filtri. [Feature/data docs](https://qlib.readthedocs.io/en/latest/component/data.html#feature), [Alpha158 docs](https://qlib.readthedocs.io/en/latest/component/data.html#data-handler)

Pattern riusabile: separare dati raw, trasformazioni condivise, trasformazioni per inferenza e trasformazioni per training; rendere espliciti gli intervalli temporali e la finestra di fit. Questo si allinea alla necessità locale di capability deterministiche, ma non autorizza a importare direttamente pandas/DataFrame nel dominio.

### Model e workflow

Il contratto modello upstream è minimale: [`BaseModel`](https://github.com/microsoft/qlib/blob/main/qlib/model/base.py) richiede `predict`; [`Model`] aggiunge `fit(dataset, reweighter)` e `predict(dataset, segment="test")`; `ModelFT` aggiunge fine-tuning. Il ciclo normale è instantiate → fit → predict, con possibilità di caricare e fine-tunare un modello. [Model docs](https://qlib.readthedocs.io/en/latest/component/model.html)

Il workflow ufficiale compone **Data → Model → Evaluation → Tracking**. YAML e Python possono assemblare componenti; la sezione `task` raggruppa `model`, `dataset` e `record`. `Recorder`/record templates salvano metriche e artefatti di training, prediction e valutazione; `SignalRecord` e `PortAnaRecord` sono esempi ufficiali. [Workflow docs](https://qlib.readthedocs.io/en/latest/component/workflow.html), [Recorder docs](https://qlib.readthedocs.io/en/latest/component/recorder.html), [workflow source](https://github.com/microsoft/qlib/tree/main/qlib/workflow), [record templates](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py)

Qlib include implementazioni benchmark per LightGBM, XGBoost, CatBoost, MLP, LSTM/GRU, attention/graph/Transformer e altri modelli, oltre a esempi RL per order execution. Sono capacità disponibili upstream, non una ragione per esporre il catalogo modelli direttamente agli agenti locali. [README, Framework](https://github.com/microsoft/qlib#framework-of-qlib), [model package](https://github.com/microsoft/qlib/tree/main/qlib/contrib/model), [RL docs](https://qlib.readthedocs.io/en/latest/component/rl/quickstart.html)

## 3. Confronto con i contratti locali

| Contratto trading-agent | Qlib | Valutazione |
|---|---|---|
| `MarketDataProvider` / provider seam | Loader, provider URI, data server e conversione a storage Qlib | **Compatibile solo come adapter:** Qlib non deve diventare il seam. Un adapter deve tradurre il risultato nel contratto locale. [Local interface](/home/luca/trading-agent/data/interface.py), [Qlib data docs](https://qlib.readthedocs.io/en/latest/component/data.html) |
| `PriceBar` normalizzato, UTC, `Decimal`, `source`, `collected_at`, `raw_payload` | Feature tabellari/pandas e storage `.bin`; i dati sono tipicamente numerici e modellistici | **Non equivalente:** Qlib non sostituisce il modello locale di osservazione e provenance. La conversione deve essere esplicita e non perdere source, timestamp, payload o precisione richiesta. [Local model](/home/luca/trading-agent/data/models.py), [Qlib data docs](https://qlib.readthedocs.io/en/latest/component/data.html) |
| SQLite come primo hub, dedup/provenance | Caching, file storage, online data server, Recorder/MLflow e backend configurabili | **Complementare, non sostitutivo:** persistiamo acquisizione e provenance nel DB locale; Qlib può consumare un export/adapter e registrare artefatti di ricerca separatamente. [Local architecture](/home/luca/trading-agent/docs/architecture.md), [Qlib workflow](https://qlib.readthedocs.io/en/latest/component/workflow.html) |
| Capability deterministiche | Processor, expression engine, dataset split e workflow configurabili | **Pattern riusabile:** feature e trasformazioni pure/versionate dietro capability proprie. Non esporre configurazione dinamica Qlib come API agente. [Data docs](https://qlib.readthedocs.io/en/latest/component/data.html), [local strategy state](/home/luca/trading-agent/analysis/strategy_state.py) |
| `StrategyProfile` / `StrategyDefinition` | Configurazione model/dataset/strategy e task YAML | **Boundary necessario:** Qlib configura il motore; il profilo strategico locale resta la fonte di identità, timeframe, direzione e parametri. [Local strategy state](/home/luca/trading-agent/analysis/strategy_state.py), [workflow docs](https://qlib.readthedocs.io/en/latest/component/workflow.html) |
| `ResearchState`, `InvestmentState`, `TradeIntent` | Dataset/model/prediction/backtest outputs e recorder artifacts | **Non sostitutivi:** Qlib produce evidenza quantitativa; non definisce la tesi strutturata, il gate di rischio, l'intento di trade o l'esecuzione deterministica del trading-agent. Fonte locale: `../trading-agent-wiki/wiki/system/investment/state-schemas.md`; [Qlib record templates](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py) |

Il link della riga `State schema wiki` è intenzionalmente da sostituire con il link di pubblicazione della wiki se il vault viene pubblicato: la fonte normativa corrente è `../trading-agent-wiki/wiki/system/investment/state-schemas.md`, non un file del repository.

## 4. Costi di adozione

1. **Dipendenze e superficie runtime.** Il `pyproject.toml` upstream richiede, oltre a numpy/pandas/PyYAML, MLflow, Redis, MongoDB client, LightGBM, gym, CVXPY, joblib, matplotlib/Jupyter, PyArrow, pydantic-settings e altri pacchetti; extra separati aggiungono PyTorch/Tianshou, Plotly e tool di sviluppo. [Upstream `pyproject.toml`](https://github.com/microsoft/qlib/blob/main/pyproject.toml)
2. **Data engineering.** I dati non sono semplicemente OHLCV in ingresso: servono conversione nel formato Qlib, provider URI/layout e, per PIT, collector e file/index dedicati. [Data preparation](https://qlib.readthedocs.io/en/latest/start/getdata.html), [PIT](https://qlib.readthedocs.io/en/latest/advanced/PIT.html)
3. **Operabilità.** Workflow, Recorder e artifact storage introducono un secondo ciclo di vita per esperimenti, metriche e modelli. È utile per ricerca riproducibile, ma duplica il ruolo del nostro SQLite se usato come persistenza primaria. [Workflow](https://qlib.readthedocs.io/en/latest/component/workflow.html), [Recorder](https://qlib.readthedocs.io/en/latest/component/recorder.html)
4. **Compatibilità di dominio.** Qlib è orientato a dataset tabellari/time-series e ricerca quantitativa; l'adattamento a `Decimal`, provenance per barra, contratti state annidati e TradeIntent richiede codice di confine e test propri. [DataHandler source](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py), [Model source](https://github.com/microsoft/qlib/blob/main/qlib/model/base.py)

## 5. Pattern da riusare e anti-pattern

### Riutilizzare

- **DataHandler a stadi:** raw → infer → learn con processor fit-tati solo sul periodo ammesso; è un buon pattern per prevenire leakage. [handler.py](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py)
- **Dataset nominati per segmenti temporali** e finestre rolling/time-series, da tradurre in capability locali deterministiche. [Dataset source](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/__init__.py)
- **Workflow con artefatti e metriche:** conservare configurazione, modello, predizioni, report e backtest come evidenza versionata. [workflow docs](https://qlib.readthedocs.io/en/latest/component/workflow.html), [record_temp.py](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py)
- **PIT per dati revisionabili**, quando il progetto introdurrà fondamentali o altri dati con publication date. [PIT docs](https://qlib.readthedocs.io/en/latest/advanced/PIT.html)

### Evitare

- Usare Qlib come provider implicito o lasciare che `provider_uri`, loader e conversione diventino il contratto del core: viola il provider seam e rende nascosta la provenance. [Qlib data docs](https://qlib.readthedocs.io/en/latest/component/data.html), [local interface](/home/luca/trading-agent/data/interface.py)
- Passare DataFrame/Qlib objects attraverso agenti, `InvestmentState` o `TradeIntent`: gli agenti devono ricevere capability e risultati normalizzati, non il framework. [Qlib model docs](https://qlib.readthedocs.io/en/latest/component/model.html), [local architecture](/home/luca/trading-agent/docs/architecture.md)
- Confondere `SignalRecord`/`PortAnaRecord` con un audit di ordini o con un risk gate: sono record di ricerca/backtest, non il contratto locale di execution. [record_temp.py](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py)
- Importare l'intero stack per ottenere solo indicatori o backtest semplici: prima usare le capability pure locali; Qlib va valutato solo per il valore incrementale di dataset/model/workflow.

## 6. Stima prudenziale del codice evitabile

Questa è una **stima interna**, non una metrica dichiarata da Qlib e non una promessa di risparmio:

- **Codice eliminabile oggi: 0 righe.** Il repository non ha ancora un equivalente locale del model/workflow/backtest di Qlib; adottare Qlib non consente quindi di cancellare codice già scritto senza prima implementare e confrontare un'integrazione.
- **Ordine di grandezza futuro: circa 150–300 righe** di plumbing locale potenzialmente evitabile per feature/dataset/model/backtest, se Qlib dimostrasse di coprire quei requisiti senza perdere i contratti locali. La stima è basata sulla futura superficie prevista dal piano e sulle responsabilità documentate in `DataHandler`/`Dataset`, `Workflow` e `Recorder`, non su una promessa upstream né su una riduzione cosmetica.
- **Costo da sottrarre: circa 100–200 righe** per adapter, configurazione, conversione dati, serializzazione dei risultati e test di compatibilità resterebbero comunque necessari; sono anch'esse stime interne, non conteggi upstream. Il saldo netto è quindi incerto e potrebbe essere nullo o negativo per un MVP che usa solo indicatori e backtest semplici.

La decisione non deve quindi essere presa sul numero di righe risparmiate, ma sul valore incrementale verificato di dataset/model/workflow rispetto alle capability locali.

## 7. Decisione proposta

**Stato: proposta, non implementata.** Mantenere Qlib fuori dal percorso MVP provider → normalizzazione → SQLite → capability deterministiche. Preparare eventualmente un modulo `quantitative research` interno con un adapter Qlib sperimentale che:

- riceva dati dal nostro contratto o da un export esplicito e versionato;
- produca risultati serializzabili con identificativo di strategia, intervallo, feature/model version, periodo e provenance;
- non modifichi `PriceBar`, `MarketDataProvider`, SQLite, `StrategyProfile`, `ResearchState`, `InvestmentState` o `TradeIntent`;
- sia valutato con benchmark di installazione, conversione dati, riproducibilità, leakage/PIT, latenza e qualità del backtest contro le capability locali.

La licenza MIT è compatibile in linea generale con studio e riuso, ma ogni codice copiato deve conservare copyright/license notices e va verificata la licenza delle dipendenze e dei dati: la licenza del repository non concede diritti sui dataset/provider esterni. [Qlib LICENSE](https://github.com/microsoft/qlib/blob/main/LICENSE), [Qlib README data preparation](https://github.com/microsoft/qlib#data-preparation), [Qlib pyproject](https://github.com/microsoft/qlib/blob/main/pyproject.toml)

## Fonti ufficiali consultate

- [Qlib GitHub repository](https://github.com/microsoft/qlib)
- [Qlib latest release v0.9.8](https://github.com/microsoft/qlib/releases/tag/v0.9.8)
- [Qlib README](https://github.com/microsoft/qlib#readme-ov-file)
- [Qlib documentation](https://qlib.readthedocs.io/en/latest/)
- [Data component docs](https://qlib.readthedocs.io/en/latest/component/data.html)
- [Workflow component docs](https://qlib.readthedocs.io/en/latest/component/workflow.html)
- [Model component docs](https://qlib.readthedocs.io/en/latest/component/model.html)
- [Point-in-time docs](https://qlib.readthedocs.io/en/latest/advanced/PIT.html)
- [Qlib `pyproject.toml`](https://github.com/microsoft/qlib/blob/main/pyproject.toml)
- [Qlib `DataHandler`](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py)
- [Qlib `Model`](https://github.com/microsoft/qlib/blob/main/qlib/model/base.py)
- [Qlib record templates](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py)
