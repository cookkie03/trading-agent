---
title: Prior-art benchmark for quantitative and agent modules
status: research
updated: 2026-11-02
---

# Prior-art benchmark

**Stato:** ricerca upstream completata il 2026-11-02. Questo documento registra fatti e proposte; non autorizza l'adozione di dipendenze o codice esterno.

## Sintesi

| Repository | Pattern utile | Confine locale | Stima prudente |
|---|---|---|---:|
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | topologia multi-agent e state condiviso | `agents/` e `workflows/`; non data layer o execution | 100–250 LOC future |
| [Qlib](https://github.com/microsoft/qlib) | data → handler → processor → dataset, workflow e recorder | adapter opzionale di quantitative research | 100–250 LOC future |
| [QuantLab](https://github.com/caalopezgo/quantlab) | feature pure, segnali point-in-time, risk override, next-open e walk-forward congelato | capability/backtest proprio, non copia sorgente | 150–300 LOC future |
| [vectorbt](https://github.com/polakowo/vectorbt) | simulazione veloce di ordini/segnali, costi e metriche | adapter benchmark; replay canonico separato | 150–300 LOC future |

Le stime descrivono codice futuro evitabile o plumbing non scritto, non righe eliminabili dal repository corrente. Non si contano come risparmio SQLite, provenance, modelli normalizzati, indicatori o contratti di dominio: nessuna repository li sostituisce senza perdere requisiti locali.

## Confronto statico riproducibile — 2026-11-02

Baseline locale esaminata: `58358d403d18bc7af6a64ac6cf2ed2313779710f`. Ispezione statica di revisioni upstream fissate; nessuna libreria esterna è stata eseguita o installata e non è stata dimostrata parità runtime. **Risparmio netto di LOC locali verificato: 0**. Le stime precedenti riguardano soltanto plumbing futuro potenzialmente evitabile, non codice eliminato.

| Repository e revisione | Confronto con la codebase | Vincolo |
|---|---|---|
| [TradingAgents `c4544913`](https://github.com/TauricResearch/TradingAgents/blob/c4544913a14ed3df5f1ed7b9e8483270ce20682a/tradingagents/graph/setup.py#L53-L89) | Il grafo ha ruoli concettualmente simili a `workflows/langgraph_workflow.py`; il PM LLM non sostituisce `execution/risk.py` e il gate deterministico. | Apache-2.0; mantenere condizioni e attribuzione in caso di riuso. |
| [Qlib `54355232`](https://github.com/microsoft/qlib/blob/54355232463878d2eebb91fe0ee5fa7fa1f5976c/qlib/contrib/data/handler.py#L98-L153) | Feature e dataset non sono dimostrati equivalenti agli indicatori `Decimal` e all'outbox con provenance locali. | MIT; adapter, dipendenze e test di equivalenza comportano costi aggiuntivi. |
| [QuantLab `ccb93d85`](https://github.com/caalopezgo/quantlab/blob/ccb93d85c27c4506b1d042fe37bb48794b9b7fa9/quantlab/backtest/engine.py#L130-L203) | Il backtest usa segnali e apertura successiva; non è dimostrata equivalenza col ciclo hourly locale. | Nessuna licenza software identificata nella revisione esaminata; non copiare senza chiarimento. |
| [vectorbt `70da8fe7`](https://github.com/polakowo/vectorbt/blob/70da8fe7c2a57948ca065ac362fc416bcf31458c/vectorbt/portfolio/base.py#L1624) | Simulazione vettoriale utile per benchmark futuro, non sostituto verificato di paper execution, risk e provenance. | [Apache-2.0 con Commons Clause](https://github.com/polakowo/vectorbt/blob/70da8fe7c2a57948ca065ac362fc416bcf31458c/LICENSE.md#L1-L13); verificare l'uso previsto. |

Le differenze di timing, costi, warm-up, precisione e provenance richiedono golden test su un dataset comune prima di dichiarare equivalenza o risparmi netti. Non sommare scenari ipotetici a LOC effettivamente rimosse.

## Decisioni di riuso

- **TradingAgents:** riusare eventualmente pattern di topologia dopo verifica della versione upstream e della licenza Apache-2.0. Gli agenti ricevono capability locali, non SDK/provider.
- **Qlib:** mantenere `PriceBar`, provenance e SQLite come contratti locali. Valutare Qlib solo dietro un adapter, perché storage e dipendenze upstream sono più pesanti dello scope MVP.
- **QuantLab:** adottare come riferimento progettuale il ciclo point-in-time e il veto del risk engine. Il repository non espone una licenza verificata nella revisione; non copiare codice senza autorizzazione.
- **vectorbt:** usarlo per ricerca e benchmark vettoriale (`from_orders`, `from_signals` o adapter equivalente). Non usarlo come sostituto del replay event-driven: la parità live/backtest, la provenance e il ciclo Exchange Module restano responsabilità locale. La licenza upstream Apache-2.0 con Commons Clause richiede una verifica legale prima della distribuzione.

## Vincoli locali preservati

- MVP: US equities, USD-only, long-only, hourly trend-following come contesto di ragionamento.
- DB hub centrale, adapter sostituibili, calcoli deterministici e LLM fuori da risk/execution.
- Backtest ufficiale e paper execution devono condividere il ciclo applicativo; benchmark veloci sono separati e dichiarati.
- Ogni risultato deve conservare dataset, timestamp, cost model, versione formula e provenance.

## Prossima integrazione

Prima di introdurre qualunque dipendenza prior-art, implementare un'interfaccia locale minimale per quantitative research/backtesting e testarla con un fake. Solo un secondo adapter reale giustifica il seam; nessun adapter vectorbt/Qlib entra nel core finché non esiste un benchmark riproducibile e una schema review.

## Fonti

- [TradingAgents](https://github.com/TauricResearch/TradingAgents)
- [Qlib data](https://qlib.readthedocs.io/en/latest/component/data.html)
- [Qlib workflow](https://qlib.readthedocs.io/en/latest/component/workflow.html)
- [QuantLab architecture](https://github.com/caalopezgo/quantlab/blob/main/docs/ARCHITECTURE.md)
- [vectorbt Portfolio API](https://vectorbt.dev/api/portfolio/base/)
- [vectorbt low-level simulation](https://vectorbt.dev/api/portfolio/nb/)
- [vectorbt license](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md)
