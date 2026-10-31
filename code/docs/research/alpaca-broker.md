# Alpaca per il Broker MVP

Ricerca del 2026-10-30, fonti primarie ufficiali. Ambito: azioni USA in USD, conto personale paper. Nessuna installazione SDK, chiamata autenticata o operazione di trading eseguita. Le proposte sotto non sono decisioni approvate né comportamento implementato. Contesto locale consultato: wiki, piano operativo, architettura, decision-log, board ed execution.

## Prodotto, ambiente e credenziali

- Per gestire il proprio conto si usa **Trading API**, con `alpaca.trading.client.TradingClient(api_key, secret_key, paper=True)`. Il default SDK è paper, ma conviene renderlo esplicito. `url_override` può cambiare il target: proposta iniziale, non esporlo nella configurazione ordinaria. [TradingClient](https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html).
- Trading paper: `https://paper-api.alpaca.markets`, live: `https://api.alpaca.markets`; Trading API v2. Chiavi paper e live sono diverse. Autenticazione diretta tramite header `APCA-API-KEY-ID` e `APCA-API-SECRET-KEY`. Market Data usa invece `https://data.alpaca.markets`, anche per il conto paper. [Autenticazione](https://docs.alpaca.markets/us/docs/authentication), [paper](https://docs.alpaca.markets/us/docs/paper-trading).
- **Broker API** è il prodotto per costruire servizi di brokerage per propri utenti, con apertura/gestione dei loro conti. Il nostro concetto Python `Broker` non implica l'uso di quel prodotto. [About Broker API](https://docs.alpaca.markets/us/docs/about-broker-api).
- Dati di mercato e capacità di inviare ordini sono confini distinti. Feed, autorizzazioni e rate limit dei dati dipendono dal piano; Basic offre copertura equity real-time IEX, non l'intero mercato. Non dedurre disponibilità SIP dalla presenza di credenziali trading. [Market Data API](https://docs.alpaca.markets/us/docs/about-market-data-api).

## Letture disponibili

| Necessità | Metodo SDK | Contenuto / cautela |
|---|---|---|
| Conto | `get_account()` | Stato, buying power e day trades; non scambiare cash e buying power. [Account](https://alpaca.markets/sdks/python/api_reference/trading/account.html) |
| Posizioni | `get_all_positions()`, `get_open_position(symbol)` | Posizioni aperte; la seconda chiamata può fallire se assente. [Positions](https://alpaca.markets/sdks/python/api_reference/trading/positions.html) |
| Ordini | `get_orders(filter)` | Filtri espliciti per evitare una vista parziale involontaria. [Orders](https://alpaca.markets/sdks/python/api_reference/trading/orders.html) |
| Strumenti | `get_all_assets(filter)`, `get_asset(symbol)` | Presenza nel catalogo non implica negoziabilità: controllare `tradable`. [Assets](https://alpaca.markets/sdks/python/api_reference/trading/assets.html) |
| Mercato | `get_clock()` | Timestamp, apertura corrente, prossima apertura/chiusura. [Clock](https://alpaca.markets/sdks/python/api_reference/trading/clock.html) |

Il modello Asset espone anche `asset_class`, `status`, `marginable`, `shortable`, `easy_to_borrow`, `fractionable`; Position distingue `qty` da `qty_available` al netto degli ordini aperti. Quantità/importi sono spesso stringhe nelle risposte: proposta, normalizzare con `Decimal` e conservare valuta e timestamp UTC. [Modelli SDK](https://alpaca.markets/sdks/python/api_reference/trading/models.html).

## Invio, ricerca, cancellazione e sostituzione

Il client ufficiale implementa `submit_order(request)` su POST `/v2/orders`, `get_order_by_id(id)`, `get_order_by_client_id(client_id)` su `/v2/orders:by_client_order_id`, `cancel_order_by_id(id)` e `replace_order_by_id(id, request)`. Questi metodi sono operazioni sul broker, non validazioni della strategia. [Sorgente TradingClient](https://github.com/alpacahq/alpaca-py/blob/master/alpaca/trading/client.py), [reference ordini SDK](https://alpaca.markets/sdks/python/api_reference/trading/orders.html).

`client_order_id` identifica l'ordine ed è ricercabile; la reference POST corrente ammette fino a 128 caratteri. Non equivale a una garanzia generale **exactly once**. In caso di timeout l'ordine potrebbe essere già arrivato al mercato: Alpaca prescrive di non reinviarlo e di non considerarlo cancellato prima della conferma; controllare dashboard e contattare supporto se resta ambiguo. [Create Order](https://docs.alpaca.markets/us/reference/postorder), [FAQ timeout](https://docs.alpaca.markets/us/docs/working-with-orders#faq).

**Proposta recovery:** persistere intento e ID cliente prima del POST; a risposta incerta classificare `submission_unknown`, cercare l'ordine e riconciliare account/posizioni/ordini; un singolo 404 non prova mancata esecuzione. Se l'ambiguità resta, sospendere nuove azioni per quell'intento e richiedere conferma operativa, senza generare un nuovo ID per ritentare alla cieca.

Il successo di PATCH non garantisce la sostituzione: l'originale può riempirsi prima e la sostituzione essere rifiutata. Alcuni stati pending impediscono replace; quantità frazionali non modificabili, ordini notional non-IPO non sostituibili. Conservare legami fra vecchio e nuovo ordine. [Replace Order](https://docs.alpaca.markets/us/reference/patchorderbyorderid-1).

## Limit con SL/TP: vincoli e lacune

Per il requisito wiki «limit + SL + TP obbligatori», bracket è il candidato: ingresso con `order_class=bracket`, TP `limit_price`, SL `stop_price` ed eventuale `limit_price` per stop-limit. Uscite attive solo dopo fill **completo** dell'ingresso; una cancella l'altra, ma entrambe possono riempirsi in mercati molto rapidi. Cancel di una gamba cancella le altre aperte; TP parziale adegua la quantità SL. TIF `day`/`gtc`, extended hours vietate; TP sopra SL per buy, viceversa sell. Stop distante almeno $0,01 dal base price applicabile. Prezzi limit/stop: massimo 2 decimali da $1, 4 sotto $1. Le gambe sono recuperabili con `nested=true`. [Orders at Alpaca](https://docs.alpaca.markets/us/docs/orders-at-alpaca).

**Proposta primo ordine:** quantità intera positiva, ingresso limit, bracket, `extended_hours=False`; scegliere esplicitamente `day` o `gtc` secondo la durata richiesta. La policy deve affrontare il periodo con ingresso parzialmente eseguito e uscite non ancora attivate. Non dichiarare protezione continua solo perché il POST bracket è riuscito. Prima dell'invio occorrono intento persistente, controlli conto/asset, prezzi e quantità, conferma delle gambe e recovery.

Le fonti ufficiali sui **frazionali sono incoerenti**: la pagina dedicata descrive market/limit/stop/stop-limit DAY, quantità o notional (mutuamente esclusivi), asset `fractionable`, e vieta short frazionali. [Fractional Trading](https://docs.alpaca.markets/us/docs/fractional-trading). La reference POST e le docstring SDK limitano ancora quantità frazionali a market/DAY e notional a market. [POST](https://docs.alpaca.markets/us/reference/postorder), [Requests SDK](https://alpaca.markets/sdks/python/api_reference/trading/requests.html). Nessuna di queste evidenze basta a promettere bracket frazionali: proposta, escluderli dal primo slice ordini e verificarli separatamente sul paper se richiesti.

Per ordini semplici extended hours la reference corrente consente limit DAY o GTC; non trasferire questa capacità al bracket. [POST](https://docs.alpaca.markets/us/reference/postorder). Gli short dipendono da disponibilità prestito e requisiti del conto: controllare flag asset correnti, non una lista statica. La documentazione richiede equity di almeno $2.000 per margin/short e distingue ETB e locates. Proposta iniziale: long-only finché la policy short non è specificata. [Margin and Short Selling](https://docs.alpaca.markets/us/docs/margin-and-short-selling), [Asset](https://alpaca.markets/sdks/python/api_reference/trading/models.html#asset).

## Lifecycle, eventi ed errori

`trade_updates` su `wss://paper-api.alpaca.markets/stream` trasmette `new`, `partial_fill`, `fill`, `canceled`, `expired`, `done_for_day`, `replaced` e ulteriori eventi di accettazione/rifiuto/pending. Il messaggio contiene l'ordine; `qty` del fill è incrementale, distinto da `filled_qty` cumulativo. `done_for_day` non equivale necessariamente a terminale definitivo. [Websocket Streaming](https://docs.alpaca.markets/us/docs/websocket-streaming). SDK: `TradingStream(..., paper=True)` e `subscribe_trade_updates(handler)`. [TradingStream](https://alpaca.markets/sdks/python/api_reference/trading/stream.html).

**Proposta riconciliazione:** mantenere stato nativo oltre alla vista normalizzata; distinguere richiesta di cancel da cancellazione confermata; non ridurre tutto a submitted/filled/rejected/cancelled. All'avvio e dopo disconnessione rileggere ordini, gambe e posizioni dal broker; deduplicare eventi e aggiornare quantità cumulative senza sommare due volte. Le fonti consultate non stabiliscono replay durevole/exactly-once per questo stream: la socket non basta come registro di verità.

Il supporto Trading/Paper pubblica **200 richieste/minuto per conto** e HTTP 429; la pagina è datata dicembre 2022, quindi trattare il valore come riferimento da riconfermare all'integrazione. Non confonderlo con i limiti di Broker API o Market Data. [Supporto Trading](https://alpaca.markets/support/usage-limit-api-calls). POST documenta 403 per buying power/azioni insufficienti e 422 per parametri non validi. [POST](https://docs.alpaca.markets/us/reference/postorder). Il REST client SDK gestisce retry configurati per codici HTTP; verificare la release effettivamente fissata prima di aggiungere altri retry esterni. [REST client ufficiale](https://github.com/alpacahq/alpaca-py/blob/master/alpaca/common/rest.py).

**Proposta errori:** preservare HTTP status/codice broker; distinguere autenticazione, validazione, indisponibilità/rate limit, risorsa assente ed esito scrittura incerto. Retry letture con budget/backoff; nessun retry generico delle scritture dopo timeout/errore di trasporto. Esito remoto sconosciuto e ordine rifiutato sono stati diversi.

## Cosa dimostra il paper

Il paper simula fill tramite quote reali, senza inviare ordini all'exchange. Non simula impatto, leakage, slippage da latenza, posizione in coda, price improvement, fee regolamentari o dividendi. Non confronta la quantità richiesta con la liquidità NBBO: può riempire quantità irrealistiche. Produce partial fill casuali nel 10% dei casi idonei. Il conto Paper Only ha dati IEX, mentre il simulatore usa NBBO: una differenza utile per capire prezzi apparentemente discordanti. [Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading).

Una futura prova paper può validare connettività, mapping e lifecycle osservato; non dimostra eseguibilità live o redditività della strategia.

## Contratto piccolo proposto e ordine dei passi

1. **Slice read-only**, coerente con [proposta architetturale](../architecture.md): `Broker.get_account()`, `get_positions()`, `get_orders(query)`. Modelli del progetto per conto/posizione/ordine, importi decimali, ID broker/cliente e stato nativo preservato; filtri, ordinamento e completezza della query espliciti. Un fake offline e un adapter Alpaca sostituibile, stesso comportamento osservabile. Assets/clock restano capacità da aggiungere quando il flusso successivo le richiede.
2. **Slice ordine paper**, separato: lookup per ID cliente, submit limit bracket e cancel; intent log durevole in execution, riconciliazione e caso timeout prima dell'uso operativo. Esempi di test: accept senza fill, fill parziale, evento duplicato, timeout dopo accettazione, cancel concorrente con fill, riavvio con gambe aperte.
3. **Replace e ulteriori capacità** solo con un caso concreto e test del relativo lifecycle. Non duplicare l'intero SDK nel contratto.

Il Broker trasporta e normalizza; execution conserva intenti, applica policy e coordina recovery. Il primo slice di lettura non richiede un ordine reale né paper. Credenziali, account attivo, feature effettivamente abilitate e release SDK restano da verificare quando si passerà all'integrazione.
