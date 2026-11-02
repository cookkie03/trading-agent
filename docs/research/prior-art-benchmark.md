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
