---
name: close-task
description: Finish a PlanMyEvents task - update knowledge files briefly and give the user the Hebrew "how to open and test" summary. Use at the end of every completed task.
---
# Close task
1. **Knowledge (short, dated, replace stale lines — no long logs):**
   - Files/functions added/moved/removed → `docs/ai/codemap.md`.
   - Business behavior/formula changed → `docs/ai/domain.md` (one line per rule).
   - Task from `docs/catering-todo/tasks/NN-*.md` → append "Outcome YYYY-MM-DD": what changed, checks run + results, what's open. Tick it in `docs/catering-todo/README.md` only with evidence.
   - `Angular/.ai/implementation_status.md`: replace the matching line in Implemented / Legacy / Known bugs / Not started / Open decisions (dated, ≤2 lines). Never append narratives there; long evidence goes in the task file.
   Max ~10 lines of doc edits per task unless the user asked for docs.
2. **Reply to the user in Hebrew**, compact:
   - מה שונה (קבצים עיקריים, 1–4 שורות)
   - איך לפתוח: URL/מסך מדויק (e.g. http://localhost:4200/events → אירוע → "בחירת מנות"); if a service is not running, the command to start it (CLAUDE.md "Commands").
   - איך לבדוק ומה התוצאה הצפויה.
   - בדיקות שהורצו בפועל (עם תוצאות) מול בדיקות ידניות מוצעות.
   - מה נשאר פתוח / שאלות.
3. Don't commit unless asked. If asked: `git -C Angular` only for frontend; FastAPI is not under git.
