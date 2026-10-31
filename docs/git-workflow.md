# Convenzione Git e workspace

Regole operative minime condivise per il progetto.

## Workspace

- Il lavoro ordinario si svolge su `main`, così Luca può seguire le modifiche direttamente da VS Code.
- Si usa un worktree separato solo se Luca lo chiede o se la modifica è radicale, sperimentale o non ancora abbastanza sicura per `main`.
- Il branch/worktree deve avere un nome breve e descrittivo, con prefisso `feat/`, `fix/`, `docs/` o `chore/` quando applicabile.

## Commit, push e merge

- Commit brevi e leggibili, preferibilmente in formato Conventional Commits: `tipo(scope): descrizione`.
- Prima del commit si eseguono i controlli pertinenti e se ne riportano i risultati.
- Il lavoro completato viene sempre pushato su GitHub.
- Il merge su `main` lo esegue Luca.
- Quando il lavoro è su un branch separato, l'agente apre autonomamente una Pull Request dopo il push, senza eseguire il merge.

## Sincronizzazione documentale

Ogni decisione o avanzamento rilevante aggiorna nella stessa sessione:

- `AGENTS.md`, se cambia il comportamento atteso degli agenti;
- la documentazione tecnica del repository, se cambia procedura o setup;
- la wiki adiacente, includendo decision log, log operativo e hot-cache quando pertinenti.

Non si pubblicano segreti, file `.env` con valori, database locali o transcript delle chat.

La wiki resta la fonte condivisa per requisiti e decisioni; il repository resta la fonte verificabile per codice, test e stato Git.
