# Struttura del progetto — alberatura approvata

Stato: alberatura approvata da Luca il 2026-10-30; creato lo scheletro dei package. Primo contratto Broker di sola lettura e adapter Alpaca paper implementati il 2026-10-31; execution e agenti ancora da sviluppare.

## Obiettivo

Codice leggibile da Luca mentre cresce, con broker, fonti dati, analisi e agenti sostituibili. La wiki adiacente conserva requisiti e decisioni; questo documento presenta una possibile organizzazione del codice. L'ordine attuale richiesto da Luca è struttura → broker Alpaca paper → ulteriori moduli.

## Alternative considerate

| Struttura | Vantaggio | Costo |
|---|---|---|
| Monolite modulare per responsabilità (proposta) | Contratti e implementazioni vicini; aggiunte locali; test offline | Occorre rispettare le dipendenze tra moduli |
| Layer generici `classes/`, `providers/`, `services/` | Primo orientamento immediato per tipo tecnico | Una funzionalità si disperde tra cartelle e `Provider` diventa ambiguo |
| Framework di plugin caricati dinamicamente | Estensioni installabili separatamente | Packaging, compatibilità e discovery da gestire prima di un caso concreto |

Proposta: monolite modulare, composizione esplicita in un punto. Rivalutare plugin dinamici solo se emergerà la necessità di installare estensioni indipendenti. Modularità non equivale a creare una classe per ogni operazione.

## Alberatura di destinazione

È una mappa di crescita, non un elenco di directory da creare subito.

```text
trading-agent/
├── .agents/skills/                 # skill di Matt Pocock e altre pertinenti
├── AGENTS.md
├── README.md
├── docs/
│   ├── architecture.md            # questa proposta
│   ├── documentation.md           # come mantenere la documentazione
│   └── research/alpaca-broker.md   # ricerca tecnica con fonti ufficiali
├── pyproject.toml                 # quando inizierà lo scaffolding
├── config/                         # impostazioni validate da ambiente
├── .env.example                   # nomi dei segreti, senza valori reali
├── agents/ · analysis/ · brokers/ · data/
├── execution/ · interface/ · storage/ · tools/ · workflows/
│   ├── execution/risk.py          # veto deterministico prima del broker
│   ├── brokers/                   # conto, posizioni, ordini; broker intercambiabili
│   │   ├── interface.py           # contratto Broker, indipendente da SDK
│   │   ├── models.py              # dati ed errori normalizzati del broker
│   │   └── alpaca.py              # AlpacaBroker, SDK confinato qui
│   ├── data/                      # acquisizione, freshness, rate limit, coordinamento
│   │   └── providers/             # fonti finanziarie e relativa normalizzazione
│   ├── storage/                   # DB, migrazioni, repository, dedup e retention
│   ├── analysis/                  # analisi e calcoli deterministici
│   │   ├── technical/             # esempi di future aree, create solo quando servono
│   │   ├── fundamentals/
│   │   └── backtesting/
│   ├── tools/                     # capacità esposte agli agenti
│   ├── agents/                    # singoli agenti, schemi, contesto e prompt
│   │   └── market/                # esempio di un agente con prompt locale
│   ├── workflows/                 # topologia LangGraph, trigger e scheduling
│   ├── execution/                 # guardrail, intent log, invio/recovery, costi e uscite
│   ├── interface/                 # CLI/UI su contratti applicativi
│   ├── config.py                  # lettura/validazione parametri e segreti
│   └── bootstrap.py               # sceglie e collega le implementazioni
└── tests/
    ├── brokers/                   # comportamento del contratto e mapping Alpaca
    ├── fakes/                     # fake offline utilizzabili dai test
    └── integration/               # prove Alpaca paper esplicite, separate dall'offline
```

`brokers/` co-localizza contratto e adapter invece di distribuire la stessa responsabilità tra più layer. La wiki suggerisce nomi diversi (`connectors`, `capabilities`, `orchestration`) ma li dichiara orientativi; qui corrispondono a broker/fonti, `analysis` e `workflows`. Il layout `src/` e il nome `trading_agent` sono approvati con questa alberatura.

## Regole che rendono la struttura modificabile

- I modelli Alpaca non escono da `brokers/alpaca.py`. Chiamanti e test usano dati del progetto.
- `brokers` parla con il broker; `execution` decide come eseguire un intento già validato, conserva l'intent e riconcilia gli esiti. Il broker non sceglie investimenti.
- `data` acquisisce e normalizza, con storico DB-first e live decision-critical con write-through secondo la wiki. `data/providers` confina gli SDK esterni: `YahooFinanceProvider` è l'adapter diretto e `OpenBBProvider` è l'adapter OpenBB; entrambi implementano `MarketDataProvider` e normalizzano OHLCV in `PriceBar`. OpenBB può delegare a un provider sottostante, ma la selezione e la provenance restano nostre. Gli agenti non chiamano vendor direttamente. `storage` persiste; non chiama vendor o LLM.
- `analysis` contiene la complessità di un'analisi; `tools` presenta agli agenti un'interfaccia piccola. Un tool complesso può usare un intero package analitico.
- `analysis.strategy_state` espone lo state comune delle valutazioni strategiche; parametri e feature restano estensibili, mentre le regole specifiche vengono validate dalla strategia concreta.
- `agents` definisce comportamenti riutilizzabili; `workflows` decide chi chiama chi, sequenza, parallelismo e state isolato per ticker/run.
- `bootstrap.py` è il punto di composizione: sceglie adapter e strumenti e li passa ai chiamanti. I moduli ricevono dipendenze invece di creare client esterni nascosti.
- Eventuali funzioni numeriche pure rimangono funzioni. Protocollo astratto soltanto dove serve sostituire un'implementazione reale, ad esempio Alpaca e fake offline.
- UI e dashboard usano contratti applicativi; il database è hub persistente, non un obbligo di far comunicare ogni chiamata Python attraverso SQL.

Esempi: aggiungere IBKR modifica `brokers` e la composizione, non gli agenti; aggiungere un'analisi di bilancio modifica `analysis/fundamentals`, il relativo tool e la sua registrazione; cambiare la topologia interessa `workflows`, mantenendo invariati i contratti degli agenti se i loro input/output restano uguali.

## Prima slice Broker: letture implementate

## Dashboard read-only

La dashboard locale vive in `openbb-ui/` come modulo sostituibile. Il backend
serve una UI responsive e contratti HTTP di sola lettura (`/health` e
`/api/dashboard`); non chiama vendor direttamente e non espone mutazioni.
L'avvio documentato è `./openbb-ui/openbb-ui`, con controllo health idempotente.
Database e OpenBB restano non collegati finché non viene implementato il
relativo read model.

1. Concordare i dati minimi di conto, posizione e ordine e il contratto di lettura: `get_account()`, `get_positions()`, `get_orders()`.
2. Con TDD, test offline dello stesso contratto con fake e adapter Alpaca tramite client sostituibile; normalizzare importi, valuta, identificatori, stati ed errori senza far trapelare SDK.
3. Eventuale prova esplicita su conto Alpaca paper per lettura, quando esistono credenziali. Nessun ordine necessario per questa slice.
4. Separatamente, aggiungere invio e cancellazione con gestione degli esiti incerti, ricerca tramite ID cliente e intent log persistente, prima di integrare gli agenti.
5. Integrare la policy limit + SL/TP del progetto, riconciliazione e guardrail: la presenza di un metodo SDK non autorizza un'operazione nella strategia.

Controlli mercato aperto e disponibilità dello strumento si aggiungono quando servono al primo flusso ordini. Il contratto cresce per casi verificabili, senza replicare l'intero SDK. Il backend backtest dovrà rispettare gli stessi contratti quando arriverà il suo slice.

Il paper trading Alpaca richiede `TradingClient(..., paper=True)` e chiavi paper; la documentazione distingue TradingClient dal prodotto Broker API. [TradingClient ufficiale](https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html), [guida Trading](https://alpaca.markets/sdks/python/trading.html). Per vincoli e lifecycle vedere [ricerca Alpaca](research/alpaca-broker.md).

## Tracciabilità alla wiki

- [Confini e sequenza](../../trading-agent-wiki/wiki/system/foundation/codebase-architecture.md), sezioni «Principio operativo», «Boundary dei package», «Slice 1».
- [Piano operativo](../../trading-agent-wiki/wiki/artifacts/piano-operativo-trading-agent.md), principi e fasi 0–1.
- [Broker ed execution](../../trading-agent-wiki/wiki/system/execution/execution.md), «Exchange — broker intercambiabili».
- [Dati e recovery](../../trading-agent-wiki/wiki/system/data/data-layer.md), freshness e riconciliazione.
- [Decisioni correnti](../../trading-agent-wiki/wiki/system/foundation/decision-log.md), precedenza delle decisioni consolidate sulle reference storiche.

I link alla wiki richiedono entrambe le repository affiancate. L'alberatura è approvata; i tre metodi Broker di lettura sono implementati e descritti in [brokers.md](brokers.md); strategia, ruolo Risk Analyst e UI non vengono risolti da questa proposta.

## Distribuzione Docker — requisito confermato

Luca richiede che il progetto sia distribuibile in produzione con Docker. Il package Python deve essere installabile nell'immagine e avviabile senza dipendenze dal percorso del Mac o dalla wiki locale.

Il rilascio dovrà includere Dockerfile e procedura di build riproducibile con dipendenze bloccate; configurazione e segreti forniti a runtime; dati persistenti esterni al filesystem effimero del container; log su stdout/stderr; processo senza privilegi e gestione SIGTERM con riconciliazione degli ordini. La modalità paper/live dovrà essere esplicita. Il database può essere un servizio separato pur mantenendo l'applicazione come monolite modulare.

Stato di questo step: packaging `src/` e `.dockerignore` presenti. Dockerfile, comando applicativo, lock delle dipendenze e validazione container arriveranno con il primo flusso eseguibile. Nessuna immagine o distribuzione produzione è attestata da questo scaffolding.

## News e desk sentiment — 2026-11-02

`AlpacaNewsProvider` normalizza titoli con fonte, URL e data; il ciclo provider può passarli al desk sentiment. Le notizie sono osservazioni, non un punteggio o una conclusione di sentiment. Copertura limitata alle prime 50 notizie della risposta: paginazione, persistenza delle fonti e sintesi LLM restano aperte. Il feed Alpaca news è stato interrogato in sola lettura; il collegamento al desk è verificato con client simulato.

## Provider e desk tecnico — 2026-11-02

`run_provider_research_cycle` acquisisce barre tramite il provider configurato, le persiste e usa la chiusura dell'ultima barra nell'intervallo richiesto come prezzo e contesto della review tecnica. Il test copre provider simulato → SQLite → desk → decisione pending → HTTP. Calcola ATR Wilder a 14 periodi dalle barre di una sola fonte, rifiutando storico insufficiente o timestamp duplicati, e sostituisce l'ATR preesistente nello state. Richiede un `as_of` esplicito e una soglia `max_age` positiva, rifiutando barre obsolete e intervalli futuri. La soglia è responsabilità del chiamante; anche la sequenza dei timestamp attesi è richiesta esplicitamente e le barre mancanti sono rifiutate. Per barre Alpaca giornaliere la sequenza può essere generata dal calendario Alpaca, usando le sessioni e la mezzanotte America/New_York come etichetta della barra; il controllo è verificato con calendario simulato. Per barre hourly il calendario genera le etichette intere sovrapposte alla sessione regolare, includendo chiusure anticipate e fuso New York; il feed può comunque comprendere dati extended-hours. La verifica delle etichette con un feed IEX reale è puntuale, non una garanzia per tutti i provider. Non sono disponibili evidenze per gli altri desk. Non è pronto per decisioni automatiche di trading.

## Evidenze desk — 2026-11-02

Il grafo di ricerca lascia `pending` la decisione quando mancano evidenze dei desk o la review tecnica è incompleta; un veto risk resta `rejected`. I desk non tecnici sono ancora placeholder senza provider: questo controllo impedisce al grafo di presentarli come una sintesi approvata, `run_research_cycle` collega il grafo a `TradeCycle` solo per decisioni approvate; l'accesso diretto al ciclo resta un seam di basso livello che richiede uno state approvato dal chiamante. I desk placeholder mantengono la pipeline in attesa. Gli esiti `pending` e `rejected` vengono registrati nel repository decisioni e sono leggibili dalla dashboard; sono audit distinti dalla decisione di invio ordine.

## Composizione paper — 2026-11-02

`workflows.paper_runtime` collega trade cycle, adapter Alpaca e repository SQLite per ordini e decisioni. La factory Alpaca usa `paper=True`, non accetta override URL e rifiuta configurazioni diverse dall'endpoint paper. È una composizione invocabile, non ancora un runtime automatico provider→agenti; persistenza e riconciliazione sono verificate offline con client simulato. Il 2026-11-02 è stato verificato anche un bracket AAPL non marketable attraverso `TradeCycle` e questa factory sul conto paper: cancellazione confermata dal broker, quantità eseguita 0, riconciliazione SQLite `CANCELLED`. Lo state e il portfolio del test erano fixture controllate, non dati di ricerca o portfolio reali; non è un E2E provider→decisione.

## Rischio condiviso — 2026-11-02

`RiskAnalyst` e `TradeCycle` usano la stessa policy provvisoria di dimensionamento ATR in `execution.risk.size_trade`, evitando una review su quantità fissa diversa dall'ordine. Il ciclo rivaluta il rischio prima dell'invio; se portfolio o prezzo cambiano, la decisione può cambiare. I parametri restano da validare in backtest. Il test offline attraversa review, ciclo, SQLite e dashboard HTTP con broker simulato: non prova un ordine Alpaca né una pipeline provider completa.

## Verifica del primo modulo — 2026-10-31

Implementati `Broker` (Protocol), modelli immutabili del progetto e `AlpacaBroker` con `get_account`, `get_positions`, `get_orders`. Lo SDK è confinato in `brokers/alpaca.py`; il contratto non ha metodi di invio o cancellazione. La lettura ordini restituisce una finestra limitata, con filtri espliciti e gambe annidate; non promette uno storico completo o uno snapshot atomico tra tre richieste.

Le factory sono paper-only; il client esplicitamente iniettato resta responsabilità del chiamante. Per il timeout HTTP dello SDK 0.44 si usa la sua sessione privata solo dentro l'adapter: versione vincolata `>=0.44,<0.45`, lock 0.44.0 e regression test dedicato. Dettagli, esempi ed errori in [brokers.md](brokers.md).

Suite offline: 25 test passati; 1 prova paper opzionale saltata per impostazione predefinita. Nessuna verifica autenticata del conto di Luca né ordini inviati. Non è un runtime di trading né una validazione del deploy Docker.
