# OpenBB e provider dati — 2026-11-04

## Risultati della ricerca

- OpenBB ODP è un toolkit open source per integrare fonti proprietarie, con licenza e pubbliche; comprende un'interfaccia Python. Non coincide necessariamente con la fonte originaria dei dati. Fonte: [OpenBB ODP](https://docs.openbb.co/odp).
- Nella versione 4 ogni fonte/provider è un'estensione indipendente; `openbb-yfinance` è il connettore Yahoo Finance. Le condizioni, la copertura e la qualità della fonte vanno valutate separatamente. Fonte: [provider OpenBB v4](https://docs.openbb.co/odp/v4/python/extensions/providers).
- La documentazione della versione 5 elenca `openbb-yfinance` fra i provider non inclusi e precisa che le ultime versioni v4 richiedono `openbb-core` 1.x, incompatibile con core 2.x. Non assumere quindi che un aggiornamento a v5 conservi questa integrazione. Fonte: [provider OpenBB v5](https://docs.openbb.co/odp/python/extensions/providers).
- La selezione di un provider non dimostra un fallback automatico in caso di errore o dati obsoleti: definire e verificare separatamente tale policy. Fonte: [preferenze e default OpenBB v5](https://docs.openbb.co/odp/python/user-guide/preferences-and-defaults).

## Stat

Il progetto dichiara `openbb>=4,<5` come extra opzionale e `yfinance` come dipendenza diretta (`pyproject.toml`); l'adapter `OpenBBProvider` e lo script di ingestion usano `yfinance` come provider predefinito. Questo descrive configurazione e codice, non una verifica live di disponibilità, qualità, licenza o funzionamento dei servizi. OpenBB come percorso principale dei dati non implica che Yahoo sia escluso come fonte sottostante.
