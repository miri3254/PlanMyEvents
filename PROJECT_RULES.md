# Project Rules & Collaboration Guide

## Purpose
This document captures working agreements, coding standards, and collaboration tips for the PlanMyEvents project. Update it whenever new expectations emerge.

## Communication
- Prefer clear, concise English; add parallel Hebrew notes if critical for stakeholders.
- Document decisions in pull requests or this file to keep historical context.
- Flag blockers early in the team chat with actionable details.
- When the user’s prompt includes language-learning requests, lead the reply with feedback on grammar, spelling, and provide a polished version of the prompt before addressing the main task.



## Workflow
- Work on feature branches named using the pattern `<issue-id>-short-description`.
- Keep commits focused; include a one-line summary plus rationale when the change is not obvious.
- Run linting and unit tests locally before opening a pull request.
- Reference related issues or tickets in commit messages and PR descriptions.

## Coding Standards
- Align with Angular style guidelines and TypeScript strict mode practices.
- Co-locate component templates, styles, and tests under the same directory.
- Prefer PrimeNG components already adopted in the project when adding UI controls.
- Write short, well-named methods; add comments only for non-obvious logic or domain decisions.

## UI/UX Guidelines
- Maintain RTL compatibility; test both Hebrew and English content whenever possible.
- Keep the visual language consistent with existing components (colors, spacing, iconography).
- Provide responsive layouts for breakpoints at 1024px and 768px.

## Testing
- Add or update unit tests when fixing bugs or introducing features.
- Use descriptive `it` statements that explain behavior, not implementation.
- For manual QA, document steps and expected results in PR descriptions or an accompanying checklist.

## Change Review
- Request reviews from at least one teammate familiar with the affected area.
- Be receptive to feedback and capture follow-up tasks if something must ship later.

## Maintenance
- Regularly prune unused assets, styles, and feature flags.
- Schedule dependency upgrades quarterly; note breaking changes and mitigation steps.

---
Feel free to expand or adjust these rules as the team evolves.
