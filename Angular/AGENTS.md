# Angular agent instructions
Read `../AGENTS.md`, then `.ai/project_architecture.md`, `.ai/angular_rules.md` and the relevant task/status sections.
This is Angular 20 standalone, not an AppModule/features-modules application.
Active API services live in `src/app/services/api-*.service.ts`; BaseApiService is in core/services.
Do not follow historical instructions claiming core/services/event.service.ts owns all data; that path does not exist.
Commands run from this directory: `npm run build`; `npm test -- --watch=false --browsers=ChromeHeadless` with a task-specific include where appropriate.
Preserve the user's existing uncommitted changes. Update .ai documentation when changing contracts or business behavior.
