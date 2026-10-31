# Trading Agent

## Wiki prima di ogni attività

Per ogni richiesta relativa a questo progetto, prima di proporre soluzioni, progettare, modificare codice, configurare servizi o eseguire operazioni, consulta la wiki locale in `../trading-agent-wiki/`.

1. Leggi `../trading-agent-wiki/CLAUDE.md`, `wiki/_meta/hot-cache.md` e `wiki/overview.md` nella wiki per recuperare regole e contesto.
2. Usa `wiki/_meta/index.md` e una ricerca mirata per trovare e leggere le pagine pertinenti alla richiesta. Per sviluppo e architettura consulta anche `wiki/artifacts/piano-operativo-trading-agent.md`, `wiki/system/foundation/codebase-architecture.md`, `wiki/system/foundation/decision-log.md` e `wiki/artifacts/project-board.md`.
3. Basa il lavoro sui requisiti pertinenti e sulle istruzioni correnti di Luca. Segnala le contraddizioni che incidono sulla richiesta; distingui decisioni consolidate, proposte e reference storiche.
4. Verifica nel repository il comportamento effettivo: la wiki descrive specifiche e decisioni, non dimostra che codice, test o deploy funzionino. Il codice preesistente è materiale da valutare rispetto al piano di ripartenza; conserva quanto presente finché il lavoro richiesto non ne definisce la destinazione.
5. Registra nella wiki decisioni e avanzamenti rilevanti, seguendo la sua taxonomy e le regole di board, log e hot-cache.

Il codice Python vive in questo repository; documentazione, decisioni e backlog condivisi vivono nella wiki adiacente. Se la wiki non è accessibile, rendi esplicita la lacuna prima di procedere con attività che dipendono dai suoi requisiti.

## Skill di Matt Pocock

Conserva le skill installate in `.agents/skills/` e i relativi collegamenti. Per il lavoro sul progetto usa le skill pertinenti di Matt Pocock quando disponibili: `codebase-design` per interfacce e moduli, `domain-modeling` per concetti e terminologia, `tdd` per implementazione e test, `code-review` per revisioni, `writing-for-agents` per istruzioni agli agenti. Leggi la skill prima di applicarla.

## Consultazione e documentazione durante lo sviluppo

Quando lavori con sub-agent, assegna a un consulente dedicato le domande sulla wiki: le sue risposte devono derivare esclusivamente dalla wiki locale e indicare pagine e passaggi pertinenti. Usa il suo contesto per il lavoro sul codice; mantieni distinta la ricerca esterna sulla documentazione dei provider. Nelle sessioni successive ricrea il consulente se quello precedente non è disponibile.

A ogni modifica rilevante aggiorna insieme al codice i documenti interessati: README per avvio/stato, `docs/architecture.md` per struttura e dipendenze, ricerca tecnica per vincoli dei servizi, wiki per requisiti/decisioni/board/log/hot-cache. Distingui proposte, implementazioni e verifiche eseguite. Usa un sub-agent dedicato alla documentazione quando disponibile; le istruzioni di manutenzione sono in `docs/documentation.md`.

## Convenzione Git e workspace

Per commit, push, merge, Pull Request e uso dei worktree, segui `docs/git-workflow.md`.
