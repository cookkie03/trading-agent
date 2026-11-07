# Strategy state

Stato: **contratto iniziale implementato e verificato** il 2026-11-01. Non è ancora lo schema LangGraph finale.

## Scopo

`StrategyState` rappresenta una valutazione deterministica di un simbolo per una specifica strategia e run. La struttura comune resta stabile mentre ogni strategia porta i propri parametri in `StrategyDefinition.parameters` e le proprie feature in `MarketContext.features`.

Questo evita di codificare nel contratto campi come `sma_20`, che appartengono alla definizione/versione della strategia e alla provenance del segnale, non all'identità dello state.

## Contratto corrente

- `StrategyDefinition`: identità, famiglia, timeframe, modalità direzionale e parametri versionati.
- `MarketContext`: prezzo di riferimento, source watermark e feature numeriche.
- `Signal`: direzione (`long`, `short`, `flat`), score normalizzato tra -1 e 1 e motivazione.
- `RiskPlan`: stop loss e quantità per segnali non flat.
- `StrategyState`: `run_id`, simbolo, data di valutazione, definizione, contesto, segnale e piano rischio.

`is_ready_for_trade()` considera pronto uno state `flat` senza piano rischio; un segnale operativo richiede un `RiskPlan`. Le regole specifiche della strategia rifiutano direzioni incompatibili, ad esempio `short` per `long_only`.

## Esempio MVP

```python
StrategyDefinition(
    key="trend-following-hourly",
    version="0.1",
    family="trend_following",
    timeframe="1h",
    direction_mode="long_only",
    parameters={"fast_window": 20, "slow_window": 50},
)
```

Le finestre, gli indicatori e le regole operative appartengono alla definizione versionata della strategia; verranno chiusi nel protocollo di backtest. Il contratto è deliberatamente più generico per supportare, in seguito, mean reversion, pairs trading o strategie multi-feature senza cambiare la forma base.

## Limiti consapevoli

- Non serializza ancora lo state per LangGraph o SQLite.
- Non contiene ancora provenance individuale per ogni feature, costi, portfolio context o audit trail.
- Non autorizza ordini: il risk gate e l'execution sono moduli successivi.
- `parameters` e `features` sono flessibili ma devono ricevere una validazione specifica quando verrà implementata una strategia concreta.

Pagine correlate: `wiki/system/investment/state-schemas.md`, `wiki/strategy/index.md`, `wiki/system/quant/quant-backtesting.md`.
