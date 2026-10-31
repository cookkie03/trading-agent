# Yahoo Finance — adapter dati storico

Stato: implementazione MVP del 2026-10-31. L'adapter è disponibile per OHLCV storico; non è una validazione di Yahoo Finance come fonte produttiva.

## Confine dell'adapter

`YahooFinanceProvider` implementa il contratto interno `MarketDataProvider` e restituisce `PriceBar`. Il resto del codice non riceve oggetti pandas né chiama direttamente `yfinance`.

La prima capability è:

```python
get_ohlcv_history(symbol, start, end, interval="1d")
```

- `start` è incluso e `end` è escluso, come documentato da yfinance;
- le date devono avere timezone;
- i timestamp restituiti sono normalizzati in UTC;
- `interval` conserva il timeframe richiesto, per evitare collisioni nello storage;
- i valori numerici diventano `Decimal`;
- il provider registra `source="yahoo_finance"` e `collected_at`;
- `auto_adjust=False` conserva i valori OHLC restituiti senza aggiustamento automatico;
- `actions=False` esclude dividendi e split da questa prima capability.

## Limiti e prossime estensioni

Questo adapter non espone ancora `info`, `fast_info`, fondamentali, dividendi, split, news, opzioni, insider data o download multi-symbol. Ognuna di queste capacità richiede un modello interno, regole di provenienza e test propri; non viene aggiunta come pass-through di yfinance.

Yahoo Finance/yfinance è quindi un adapter di sviluppo per il primo flusso dati. La documentazione ufficiale di yfinance segnala che il progetto non è affiliato a Yahoo e che l'uso delle Yahoo Finance API è destinato all'uso personale. Prima di usarlo come fonte produttiva vanno verificate licenza, stabilità, rate limit, freshness e persistenza consentita.

## Fonti ufficiali consultate

- [yfinance quick start](https://ranaroussi.github.io/yfinance/)
- [yfinance historical data reference](https://ranaroussi.github.io/yfinance/reference/yfinance.functions.html)
- [yfinance stock reference](https://ranaroussi.github.io/yfinance/reference/yfinance.stock.html)
- [yfinance repository README](https://github.com/ranaroussi/yfinance/blob/main/README.md)
