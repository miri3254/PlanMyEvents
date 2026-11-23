# Design system — implementation reference
Updated 2026-11-15.
- Authoritative CSS: Angular/src/styles.scss. Do not create parallel --color-* tokens from illustrative old docs.
- Existing tokens: --primary hsl(24, 95%, 53%), --primary-dark hsl(14, 90%, 48%), --primary-light hsl(24, 95%, 95%).
- Reuse --background, --card-bg, --foreground and existing border/status/table tokens; inspect definitions.
- Heebo, Hebrew RTL; preserve readable numbers, phones, currency and mixed-direction text.
- PrimeNG Aura: app.config.ts. Match dialogs, tables, loading overlay, toasts and dark theme.
- Keep mobile/tablet/desktop layouts usable using neighboring component patterns.
- Client wants branded print/export. Existing PDF assets: FastAPI/app/assets/blank.png, blank_pages.png and fonts/Heebo-*.ttf.
- PDF layout is FastAPI/app/utils/pdf_generator.py; screen CSS does not brand PDFs. Excel has a separate export service.
- Visually check long Hebrew notes, multipage tables, repeating headers, logos, numbers, empty optional fields and page breaks.
- Confirm audience: internal costs/stock notes must not appear in client output just because the layout is shared.
