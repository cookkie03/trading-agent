# Alpaca come vendor dati

**Ricerca su fonti ufficiali Alpaca verificata il 2026-10-31.** Questa scheda riguarda Alpaca come fonte di dati, separata dall'uso della Trading API per conto, posizioni e ordini. Piani, entitlements e condizioni commerciali possono cambiare: vanno verificati prima di ogni uso produttivo.

## Sintesi operativa

Alpaca può essere un adapter diretto del nostro `MarketDataProvider` per equities, crypto, options, news e corporate actions. Non è però una fonte universale:

- il piano Basic per equities è IEX-only, quindi non rappresenta automaticamente il mercato USA completo;
- il feed options `indicative` non equivale a OPRA: le quote sono derivate e i trade indicativi sono ritardati;
- i fundamentals non risultano documentati, nelle fonti consultate, come prodotto API dedicato equivalente a un fundamentals provider;
- le corporate actions possono arrivare o diventare disponibili in ritardo;
- la pagina ufficiale di supporto consultata afferma che i dati API Alpaca non possono essere redistribuiti.

Per il progetto: Alpaca è adatta come sorgente interna/paper-trading e come adapter candidato per dati decisionali, ma la policy di feed, freshness, entitlement e licensing deve restare nel nostro codice.

## Capacità e endpoint

| Capacità | Accesso documentato | Note per l'adapter |
|---|---|---|
| Equities storico | REST Market Data API, stock bars/trades/quotes/snapshots | Lo storico equities è documentato dal 2016; il feed va scelto esplicitamente. |
| Equities real-time | WebSocket stock stream | Basic: IEX; Algo Trader Plus: accesso SIP secondo piano. Non assumere market-wide coverage dal possesso delle credenziali. |
| Crypto storico/real-time | REST e WebSocket crypto | Lo storico crypto è l'eccezione indicata alla regola generale di autenticazione. |
| Options storico | `GET https://data.alpaca.markets/v1beta1/options/bars` e endpoint trade/quote/snapshot/chain | Copertura storica indicata da febbraio 2024. |
| Options real-time | `wss://stream.data.alpaca.markets/v1beta1/{feed}` | Feed `indicative` o `opra`; OPRA richiede entitlement. Protocollo documentato MessagePack. |
| News | `GET https://data.alpaca.markets/v1beta1/news` e WebSocket news | Filtri per simbolo/intervallo, paginazione e contenuto completo opzionale. La data storica 2015 appare in documentazione più vecchia e non va trattata come garanzia corrente. |
| Corporate actions | REST corporate actions e stream SSE | Azioni documentate: dividendi, split, fusioni, spin-off, diritti e rimozioni. Alpaca non garantisce il momento di creazione/disponibilità. |
| Fundamentals | Nessun prodotto API dedicato chiaramente identificato nelle fonti consultate | Non usare Alpaca come unico adapter fundamentals senza una verifica ulteriore o una fonte complementare. |

Fonti ufficiali:

- [About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api)
- [Getting Started with Alpaca Market Data](https://docs.alpaca.markets/docs/getting-started-with-alpaca-market-data)
- [Historical Option Data](https://docs.alpaca.markets/us/docs/historical-option-data)
- [Real-time Option Data](https://docs.alpaca.markets/us/docs/real-time-option-data)
- [Historical News Data](https://docs.alpaca.markets/us/docs/historical-news-data)
- [Real-time News](https://docs.alpaca.markets/us/docs/streaming-real-time-news)
- [Corporate actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1)
- [Corporate Actions SSE changelog](https://docs.alpaca.markets/us/v1.1/changelog/2026-07-20-corporate-actions-b7b8e98)

## Piani, feed e limiti

La pagina ufficiale Market Data consultata riporta, come valori da riverificare prima dell'uso:

| Piano | Equities | WebSocket equities | Storico/API | Options |
|---|---|---:|---:|---|
| Basic | real-time IEX | 30 simboli | dal 2016; storico SIP recente limitato agli ultimi 15 minuti | indicative |
| Algo Trader Plus | SIP secondo entitlement | simboli illimitati | 10.000 chiamate/min; nessuna limitazione SIP recente indicata | OPRA; quote WebSocket 1.000 |

Valori riportati dalla stessa documentazione: Basic 200 chiamate/min e Algo Trader Plus 10.000 chiamate/min per API storiche; options WebSocket 200 quote Basic e 1.000 quote Algo Trader Plus. La Broker API ha limiti propri e può avere limiti personalizzati per correspondent: [Broker API rate limits](https://docs.alpaca.markets/us/docs/broker-api-rate-limits).

Il feed non deve essere implicito. Il nostro adapter dovrebbe rendere espliciti `iex`, `sip` o `delayed_sip` e registrare il feed nella provenance. Senza entitlement SIP, le query storiche SIP devono rispettare il ritardo minimo documentato; gli stream non inclusi nel piano possono fallire in autenticazione. Sono documentati anche limiti sulle connessioni simultanee.

## Licensing e redistribuzione

La pagina ufficiale [Can I redistribute Alpaca API data via my platform?](https://alpaca.markets/support/redistribute-alpaca-api), indicata come novembre 2022, risponde che i dati Alpaca API non possono essere redistribuiti. Non va quindi progettato un dashboard/data product multiutente o pubblico assumendo che il piano individuale conceda tale diritto. Per redistribuzione, visualizzazione a clienti o uso commerciale serve una verifica scritta con Alpaca e degli obblighi dei provider/mercati sottostanti.

## SDK e conseguenze architetturali

Alpaca documenta SDK per [Python](https://alpaca.markets/sdks/python/), Go, Node.js e C#/.NET nella pagina [SDKs and Tools](https://docs.alpaca.markets/docs/sdks-and-tools). La parità tra SDK, endpoint recenti, feed e protocolli non è automatica: corporate-action SSE e options MessagePack devono essere verificati nella versione SDK scelta.

Il modulo diretto Alpaca futuro dovrebbe quindi:

1. implementare il contratto interno, non esporre `alpaca-py` agli agenti;
2. separare equities, news, corporate actions e options come capability interne;
3. rendere espliciti feed, piano/entitlement e timestamp di raccolta;
4. fallire in modo leggibile quando il feed non è autorizzato o la freshness non è sufficiente;
5. mantenere provenance e raw payload nello storage;
6. non offrire redistribuzione senza una decisione/licenza esplicita.

## Decisione proposta

Usare Alpaca come adapter diretto complementare a `OpenBBProvider`, iniziando da equities storico/real-time e news solo dopo aver definito i contratti interni e la policy di freshness. Tenere corporate actions come sorgente di eventi con ritardo potenziale. Non trattare Alpaca come fonte fundamentals primaria né come fonte automaticamente redistribuibile.
