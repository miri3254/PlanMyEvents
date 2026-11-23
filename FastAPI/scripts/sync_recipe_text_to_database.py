"""Attach full source-document text and provenance to existing dishes."""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from extract_recipe_documents import SOURCE, extract_docx
from match_recipe_sources import load_seed_dishes, score


DB = Path(__file__).resolve().parents[1] / "data" / "planmyevents.db"

# Names whose source title differs materially from the dish title.
OVERRIDES = {
    "סלט טונה": "סלט טונה _.docx",
    "סלט אסייתי": "מתכונים סלטים מגשי אירוח.docx",
    "גבינת שמנת בטעמים": "גבינות שמנת בטעמים_.docx",
    "טורטייה גבינות קריספית": "טורטיה במילוי גבינות וציפוי קריספי",
    "טורטייה טונה וירקות": "טורטיה בסלט טונה וירקות",
    "טורטייה סלמון מעושן": "טורטיה בסלמון מעושן וירקות",
    "קישים גדולים": "מילוי קישים - 95 יחידות גדולים.docx",
    "תפוחי אדמה מוקרמים": "תפו_א מוקרם _.docx",
    "פוקאצ'ות": "פוקאצות _.docx",
    "תפוחי אדמה פריזיאניים": "מתכונים לאירוע בשרי_.docx",
    "סלמון בעשבי תיבול": "מתכונים לאירוע בשרי_.docx",
    "סופלה שוקולד": "סופלה.docx",
    "סיגרי פילו וחלבה": "מתכונים לאירוע בשרי_.docx",
}


def choose_source(name: str, documents: list[tuple[Path, str]]) -> tuple[Path, str]:
    hint = OVERRIDES.get(name)
    if hint:
        matches = [(path, text) for path, text in documents if hint in path.name]
        if matches:
            return matches[0]
    return max(documents, key=lambda item: score(name, item[0], item[1]))


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.with_name(f"{DB.stem}_before_recipe_text_{stamp}{DB.suffix}")
    shutil.copy2(DB, backup)

    documents = [(path, extract_docx(path)) for path in SOURCE.rglob("*.docx")]
    conn = sqlite3.connect(DB)
    updated = 0
    missing: list[str] = []
    try:
        conn.execute("BEGIN")
        for name in load_seed_dishes():
            path, text = choose_source(name, documents)
            relative = path.relative_to(SOURCE)
            description = (
                f"מקור: {relative}\n"
                f"תיקייה: {relative.parent}\n"
                f"קובץ: {path.name}\n\n"
                f"{text}"
            )
            cursor = conn.execute(
                "UPDATE dishes SET description = ?, updated_at = ? "
                "WHERE name = ? AND is_deleted = 0",
                (description, datetime.now().isoformat(sep=" ", timespec="seconds"), name),
            )
            if cursor.rowcount:
                updated += cursor.rowcount
            else:
                missing.append(name)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Updated {updated} dishes; missing {len(missing)}; backup {backup}")
    if missing:
        print("Missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()
