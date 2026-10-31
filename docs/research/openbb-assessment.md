---
title: "OpenBB — valutazione multivendor"
type: research
status: active
area: software
created: 2026-10-31
updated: 2026-10-31
---

# OpenBB — spiegazione e valutazione multivendor

**Stato del documento:** ricerca ufficiale datata al 2026-10-31; la raccomandazione è una proposta tecnica per l'MVP, non una decisione chiusa né un'implementazione.

## 1. Risposta breve

OpenBB non è il fornitore dei dati e non rende automaticamente vendor agnostic il nostro sistema. È una piattaforma/toolkit open-source che installa e registra integrazioni verso provider esterni e presenta i loro dati tramite SDK Python, REST, MCP, CLI e interfacce UI/prodotti distinti.

**Raccomandazione:** mantenere il requisito vendor agnostic e scegliere **ibrido, non OpenBB-first runtime**:

- usare OpenBB come catalogo/esploratore e, solo dove conviene, come un adapter interno tra gli adapter del progetto;
- usare adapter diretti per broker, quote live, capacità con requisiti di latenza/freshness stretti e provider per i quali servono controllo fine, errori e costi;
- esporre agli agenti solo le nostre capability e i nostri modelli normalizzati;
- trattare la selezione/fallback come policy del progetto, non delegarla a OpenBB.

Questa scelta conserva l'utilità di OpenBB senza rendere il suo catalogo, i suoi namespace, le sue dipendenze o i suoi provider impliciti parte del contratto applicativo.

## 2. Prima distinzione: prodotti, piattaforma e provider

### Open Data Platform / SDK Platform

La documentazione ufficiale descrive ODP come un toolkit open-source di integrazione dati. ODP Python fornisce pacchetti per SDK, REST e MCP; ODP CLI espone l'accesso da terminale; ODP Desktop amministra ambienti Python e servizi backend. La pagina ufficiale presenta Workspace ed Excel come destinazioni analyst-facing, non come sinonimi del runtime SDK.

Quindi il percorso concettuale è:

```text
nostra capability
  -> nostro adapter OpenBB (opzionale)
      -> OpenBB Platform / ODP
          -> adapter OpenBB del provider
              -> API/servizio del provider sottostante
```

OpenBB resta un ulteriore strato software. Il provider sottostante determina disponibilità, limiti d'uso, termini del dato e spesso la chiave API.

### Aggregatore versus fornitore sottostante

OpenBB registra comandi e provider package. In V5, per esempio, `openbb-fred` espone il namespace `obb.fred` e `openbb-cboe` espone `obb.cboe`; il parametro `provider=` identifica il provider registrato. Questo non significa che OpenBB possieda o garantisca il dato: la richiesta arriva al servizio esterno e le sue regole restano applicabili.

Per il nostro dominio, la provenienza deve quindi conservare almeno:

- provider effettivo e, se applicabile, adapter OpenBB;
- timestamp di raccolta e data di riferimento;
- parametri/range e qualità/freshness osservate;
- identificativo/dedup key secondo i contratti del progetto;
- termini/licenza applicabili alla fonte sottostante.

La normalizzazione OpenBB è utile come punto di partenza, ma non va assunta come modello di dominio definitivo: il nostro modello normalizzato deve proteggere agenti, capability e persistenza dai cambi di provider e di OpenBB.

## 3. Esempio concreto: richiesta -> dato normalizzato

Richiesta applicativa: `get_ohlcv_history(AAPL, 2025-01-01, 2025-01-31)`.

```text
MarketDataCapability.get_ohlcv_history(request)
  -> policy del progetto: freshness, licenza, provider preferito/fallback
  -> OpenBBMarketDataAdapter (se scelto per questa capability)
       -> obb.<provider>.<command>(symbol="AAPL", ...)
       -> API del provider sottostante
  oppure
  -> DirectMarketDataAdapter (broker, yfinance, Twelve Data, ...)
  -> mapping nel nostro OhlcvBar + Provenance
  -> dedup/persistenza nel DB
  -> capability restituisce il modello del progetto
```

L'agente non deve conoscere `obb.fred`, `obb.cboe`, `provider=...`, SDK diretti o chiavi API. Se domani la policy passa da OpenBB/FRED a un adapter diretto, cambia il wiring e non il contratto dell'agente.

## 4. Copertura e normalizzazione

OpenBB consente di ispezionare la copertura degli integration package installati con `obb.coverage.providers`. I provider package sono installabili e rimovibili indipendentemente; dopo una modifica la documentazione richiede `openbb-build` oppure un riavvio Python per rigenerare il client.

Questo è utile per catalogare:

- quali provider/package sono disponibili nell'ambiente;
- quali comandi espongono;
- quali credenziali sono richieste;
- quali capacità possono essere candidate per una capability del progetto.

Non è sufficiente per dichiarare copertura di produzione: la copertura effettiva dipende dal provider, dal piano, dalla chiave, dal periodo/mercato e dai limiti operativi. Dovremo testare risposta, completezza, timestamp, timezone, corporate actions e semantica degli errori contro fixture nostre.

## 5. Licenza, piani, chiavi e costi

### Software OpenBB

La FAQ ufficiale V5 indica Apache-2.0 per il repository e i package V5, con obblighi di conservazione degli avvisi e documentazione delle modifiche. La documentazione storica V4 indica AGPL-3.0-only: non bisogna mescolare le due epoche né usare package V4 incompatibili con il runtime V5.

La licenza del software OpenBB non concede i diritti sul dato dei provider. Ogni fonte mantiene termini, limiti di redistribuzione e condizioni commerciali proprie.

### Provider e credenziali

La documentazione V5 mostra credenziali provider-specifiche, ad esempio `FRED_API_KEY`, e supporta assegnazione in sessione, variabili d'ambiente e `~/.openbb_platform/user_settings.json`. L'installazione non elimina la necessità di account o piani del provider.

Il progetto non deve stampare o incorporare segreti. La configurazione deve rimanere nel nostro modulo di config/adapter; il DB deve registrare provenienza e metadati, non chiavi.

### OpenBB Workspace e costi

La pagina ufficiale dei prezzi riguarda Workspace e mostra piani/prodotti separati (Community, Lite, Pro e Snowflake). Non è una prova di un prezzo per ODP Python, né rende gratuiti i provider sottostanti. Per questo assessment non assumiamo un abbonamento Workspace: il runtime candidato è ODP Python/SDK, con costi da valutare provider per provider.

## 6. Installazione e dipendenze

La documentazione V5 richiede Python `>=3.10,<4` per i package documentati. Il package `openbb-core` fornisce runtime, namespace `openbb`, REST application e `openbb-build`, ma non fornisce dati. I provider package aggiungono integrazioni e dipendenze; `openbb` è una distribuzione ombrello che installa runtime, provider elencati e tooling.

È possibile installare package selettivi, per esempio `openbb-core openbb-cboe openbb-imf`, invece dell'ombrello completo. Alcune estensioni analitiche richiedono installazione separata. La documentazione sconsiglia di mescolare package V4 e V5 e raccomanda un ambiente pulito per la migrazione.

**Implicazione architetturale:** introdurre OpenBB aggiunge un albero di dipendenze, generazione del client e vincoli di versione. Non va installato solo perché compare nel catalogo: prima serve una capability concreta per cui il suo adapter riduca davvero lavoro o aumenti copertura.

## 7. Errori e fallback: cosa OpenBB fa e cosa non fa

La documentazione ufficiale distingue, tra gli altri:

- `OpenBBError` e credenziali assenti;
- `EmptyDataError` per dati vuoti;
- `UnauthorizedError` per autorizzazione provider;
- errori di validazione degli input;
- eccezioni inattese.

Nel REST mapping questi casi possono diventare HTTP 400, 204, 502, 422 o 500. I warning possono essere restituiti nel risultato (`result.warnings`) senza essere stampati; il debug mode può preservare traceback completi.

Il cosiddetto provider fallback V5 **non è un retry resiliente**: senza provider esplicito, OpenBB sceglie il primo provider configurato/ammissibile con le credenziali richieste (altrimenti segue la lista/installazione secondo le regole documentate). Se nessuno è idoneo, riporta `Provider fallback failed.` La documentazione non descrive un passaggio automatico a un altro provider dopo un timeout, una risposta vuota, un errore di qualità o un errore di rate limit.

Per il progetto il fallback deve quindi stare nel nostro adapter/orchestrator e distinguere almeno:

1. provider non configurato/non autorizzato;
2. provider temporaneamente indisponibile o rate-limited;
3. risposta vuota ma valida;
4. risposta invalida/incompleta/stale;
5. errore non retryable o licenza insufficiente.

OpenBB può essere una strategia tra le candidate, non il decisore finale.

## 8. Versioning

V5 usa namespace provider-specifici come `obb.fred` e `obb.sec`, mentre la documentazione V4 usa namespace condivisi per asset class come `obb.equity`. Le due forme non sono intercambiabili. Inoltre package provider, client generato e core devono restare compatibili.

Il nostro adapter deve quindi:

- pin-nare le versioni nel lockfile quando e se OpenBB viene adottato;
- isolare import e namespace OpenBB in un modulo;
- avere contract test contro fake/fixture, senza chiamate autentiche nei test offline;
- mappare errori e modelli OpenBB in errori/modelli nostri;
- permettere di rimuovere OpenBB senza riscrivere capability e agenti.

## 9. Confronto delle tre strategie

| Strategia | Vantaggi | Costi/rischi | Valutazione |
|---|---|---|---|
| **OpenBB dietro nostro adapter** | Catalogo ampio, provider package già integrati, una superficie tecnica da esplorare | Dipendenze e versioning OpenBB; copertura/semantica non garantite; fallback non resiliente; doppio mapping | Buona per capability batch/storiche selezionate, dopo test |
| **SDK diretti dietro adapter nostri** | Controllo su freshness, errori, rate limit, licenza e costi; dipendenze mirate; broker/live più naturali | Più lavoro di integrazione e manutenzione per ogni provider | Necessaria per broker, live/decision-critical e casi con requisiti stretti |
| **Ibrida** | Conserva catalogo e integrazioni OpenBB dove danno leverage, senza imporre OpenBB al runtime | Richiede una policy chiara e due famiglie di adapter | Scelta raccomandata per questo MVP |

## 10. Decisione proposta e prossimi criteri

**Proposta delegata:** declassare “OpenBB-first” da regola runtime a **OpenBB-first per catalogazione e valutazione**, con adozione runtime per capability caso per caso.

Una capability può scegliere OpenBB dietro adapter solo se i test dimostrano un vantaggio concreto su copertura, tempo d'integrazione, qualità o costo totale. In ogni caso restano nostri:

- interfaccia della capability;
- modelli normalizzati e provenance;
- persistenza, dedup e retention;
- policy di freshness e fallback;
- classificazione errori e osservabilità;
- pinning/versioning e test offline.

Prima di aggiungere la dipendenza OpenBB al progetto, valutare una capability rappresentativa (per esempio fondamentali o una serie macro) con una matrice provider che registri: copertura, qualità, freshness, licenza, chiavi, costi, rate limit, failure modes, dipendenze e facilità di rimozione. Quote live e dati conto restano candidati naturali per adapter broker diretti secondo la policy wiki.

## Fonti ufficiali consultate (2026-10-31)

- OpenBB ODP overview: <https://docs.openbb.co/odp>
- Installazione ODP Python V5: <https://docs.openbb.co/odp/python/installation>
- Provider, namespace, credenziali e coverage: <https://docs.openbb.co/odp/python/extensions/providers>
- Settings e configurazione: <https://docs.openbb.co/odp/python/settings>
- Warnings ed errors: <https://docs.openbb.co/odp/python/user-guide/warnings-and-errors>
- Preferences, defaults e provider selection: <https://docs.openbb.co/odp/python/user-guide/preferences-and-defaults>
- Licenza V5 e distinzione V4: <https://docs.openbb.co/odp/python/faqs/license>
- Prezzi Workspace: <https://openbb.co/pricing/>

## Limiti della ricerca

- Le fonti ufficiali descrivono interfacce, package e regole generali; non sostituiscono test di copertura sul simbolo/periodo/capability scelti.
- Non sono state installate dipendenze, configurate chiavi o chiamate API provider.
- I prezzi e i termini dei provider sottostanti non sono deducibili dalla documentazione OpenBB e vanno verificati sui siti ufficiali dei singoli provider prima di una scelta runtime.
- Questa pagina è una proposta/ricerca; non attesta che OpenBB sia presente o funzionante nel repository.
