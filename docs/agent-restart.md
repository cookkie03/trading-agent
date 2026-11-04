# Ripartenza: definizione degli agenti

Stato: punto di partenza concordato il 2026-11-05; non descrive un'implementazione già completata. La fonte condivisa delle decisioni e dei prossimi passi è la wiki adiacente, in particolare `wiki/artifacts/project-board.md` e `wiki/artifacts/architettura.canvas`.

## Direzione

- Sei agenti distinti: Market Analyst, Sentiment Analyst, Technical Analyst, Fundamental Analyst, Risk Analyst e Portfolio Manager. I raggruppamenti nel canvas sono visivi.
- Il grafo degli agenti, i trigger che avviano i cicli e i tool hanno responsabilità distinte. La posizione del codice dei trigger e dei cicli esterni resta da definire; non introdurre cartelle `steps/` o `orchestration/` solo per anticiparla.
- Prima si verificano e sviluppano gli agenti; seguono tool, integrazioni provider e dati, quindi frontend. I filoni precedenti sono sospesi, non cancellati. Test e dipendenze simulate accompagnano lo sviluppo.
- Ricercare come rendere sostituibile il backend di esecuzione dei singoli agenti; la compatibilità con piattaforme specifiche non è ancora dimostrata.
- Il reviewer PM sperimentale è accantonato come concetto, non il Portfolio Manager. Il codice preesistente è da valutare, non da eliminare automaticamente.
- Rischio e protezioni sugli ordini restano deterministici; nessuna autorizzazione all'esecuzione con broker reale.
