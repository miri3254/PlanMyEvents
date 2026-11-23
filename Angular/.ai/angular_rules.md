# Angular rules — current implementation
Updated 2026-11-15.
- Use existing Angular 20 standalone patterns; main.ts/app.config.ts and loadComponent routes.
- Screens: src/app/components; shared UI: src/app/shared. Do not introduce features/NgModules from historical docs.
- Domain HTTP services: src/app/services; reusable BaseApiService/utilities: core/services.
- Types: core/models/api.models.ts, core/models/index.ts, core/models/enums.ts; also inspect existing models/*.model.ts consumers.
- Reuse ApiEventService/backend calculations. Do not add another localStorage business database.
- Domain formulas belong in backend services. UI previews must agree with authoritative results.
- Match neighboring selectors/naming/injection style; avoid unrelated refactors.
- Use strict typing for new code and existing RxJS teardown patterns; avoid duplicate subscriptions/stale UI.
- Use existing PrimeNG controls/toasts, Hebrew labels, RTL and theme tokens.
- Persistent fields need API/UI mappings and save round-trip checks, including null/zero/false.
- Run focused meaningful tests and build for code changes as appropriate; documentation alone needs no application suite.
- See project_architecture.md for commands and implementation_status.md for business mismatches.
