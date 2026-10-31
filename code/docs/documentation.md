# Documentazione del progetto

Stato: routine operativa richiesta da Luca il 2026-10-30. La documentazione accompagna ogni avanzamento; le proposte architetturali restano tali finché vengono concordate.

## Fonti e responsabilità

| Dove | Responsabilità | Quando aggiornare |
|---|---|---|
| `README.md` | Ingresso per chi legge il repository: scopo, stato reale, avvio e link | Quando cambiano stato, setup o percorso di lettura |
| `docs/architecture.md` | Organizzazione approvata del codice, regole di dipendenza e proposte dei contratti ancora da definire | Quando concordiamo o cambiamo contratti e struttura |
| `docs/research/` | Ricerca tecnica datata, con link alle fonti ufficiali | Quando una scelta dipende da documentazione esterna o cambiano fatti rilevanti |
| Wiki, pagine tematiche | Requisiti e decisioni condivise con motivazioni | Quando Luca decide o emergono nuovi requisiti |
| Wiki, board e hot-cache | Attività e contesto per la sessione successiva | Dopo ogni avanzamento rilevante |
| Wiki, log | Registro append-only di operazioni e limiti | Dopo ogni operazione rilevante |
| `AGENTS.md` | Regole e puntatori per gli agenti | Quando cambia la procedura di lavoro |

La wiki resta la fonte di requisiti e decisioni. Il codice, i test eseguiti e le verifiche datate attestano il comportamento effettivo. Nei documenti tecnici si collegano le pagine pertinenti della wiki per evitare copie destinate a divergere.

## Routine per ogni step

1. Consultare la wiki prima del lavoro e annotare i requisiti pertinenti. Il consulente wiki risponde da quelle fonti e segnala contraddizioni; la risposta conserva i riferimenti alle pagine.
2. Identificare se l'output è una proposta, una decisione concordata, un'implementazione o una verifica. Riportare questo stato nel documento interessato.
3. Aggiornare nello stesso step i documenti toccati dal cambiamento: contratto del modulo, esempi d'uso, configurazione e test quando esistono davvero.
4. Registrare decisioni e avanzamenti nella wiki, con owner, link di dettaglio, evidenza datata e limiti. Una suite non eseguita non diventa verde per effetto di una modifica documentale.
5. Prima di chiudere, verificare link locali, coerenza tra README e struttura presente, correttezza dei comandi documentati e `git diff --check`. Eseguire gli esempi quando esiste il relativo software; indicare esplicitamente quelli non eseguiti.

Il sub-agent documentazione prepara e aggiorna i documenti del repository; l'agente principale verifica l'allineamento con codice e wiki e coordina le scritture per evitare conflitti.

## Skill installate per la documentazione

- [`find-skills`](../.agents/skills/find-skills/SKILL.md), da [vercel-labs/skills](https://github.com/vercel-labs/skills): ricerca di skill. Installata su richiesta di Luca tramite `npx skills add https://github.com/vercel-labs/skills --skill find-skills --yes --agent codex`.
- [`readme-blueprint-generator`](../.agents/skills/readme-blueprint-generator/SKILL.md), da [github/awesome-copilot](https://github.com/github/awesome-copilot/tree/main/skills/readme-blueprint-generator): costruisce il README partendo da architettura, struttura, workflow e test. Installata project-local con `npx skills add https://github.com/github/awesome-copilot --skill readme-blueprint-generator --yes --agent codex` e applicata a questo setup.
- Le skill di Matt Pocock già presenti restano disponibili; `writing-for-agents` guida le modifiche a istruzioni per agenti, `codebase-design` le interfacce e `code-review` la revisione delle modifiche.

La skill README usa come esempi sorgenti `.github/copilot/`; qui le sorgenti effettive sono `AGENTS.md`, `docs/architecture.md` e la wiki adiacente. La convenzione del progetto prevale: non si crea una seconda copia della documentazione per imitare quei path. La skill non esegue sincronizzazione automatica né crea un sito: la manutenzione è parte del lavoro di ogni sessione.

Le installazioni sono locali in `.agents/skills/` e registrate in `skills-lock.json`, senza installazioni globali. Le nuove skill saranno scoperte dal catalogo dell'app al suo aggiornamento; in questa sessione sono state lette e applicate direttamente.
