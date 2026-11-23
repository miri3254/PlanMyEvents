# PlanMyEvents Copilot instructions
Updated from source inspection 2026-11-15.
- Read ../CLAUDE.md (short rules + token budget) and ../docs/ai/codemap.md (task→files) first; Angular/AGENTS.md and the parent AGENTS.md for detail.
- Use .ai/project_architecture.md for real paths, .ai/api_structure.md for API mapping, .ai/angular_rules.md and .ai/design_system.md for conventions.
- Read .ai/catering_requirements.md and .ai/implementation_status.md before business changes. Requirements, current behavior and open decisions are distinct.
- Task briefs: ../docs/catering-todo/README.md. Read the attached original source before coding; inspect only mapped implementation and direct dependencies.
- Angular 20 standalone uses bootstrapApplication, app.config.ts and loadComponent. Screens: src/app/components; APIs primarily: src/app/services.
- Persist business data through existing FastAPI endpoints only (the old localStorage EventService was removed).
- Keep API snake_case / UI camelCase mapping synchronized, including backup and PDFs.
- Preserve Hebrew RTL and existing PrimeNG patterns. Reuse src/styles.scss tokens.
- Run npm commands in Angular, not the parent package. Use focused checks and update knowledge files after meaningful changes.
- Preserve user changes and data. Old docs, draft emails, tests and code defaults are not newly approved client requirements.
