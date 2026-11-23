"""Match seeded dish names to their most likely source DOCX without writing data."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from extract_recipe_documents import SOURCE, extract_docx


def load_seed_dishes() -> list[str]:
    path = Path(__file__).with_name("seed_real_catering_data.py")
    spec = importlib.util.spec_from_file_location("seed_real_catering_data", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return [row[0] for row in module.DISHES]


def normalize(value: str) -> str:
    value = value.replace("תפו_א", "תפוחי אדמה")
    value = value.replace("_", " ")
    return re.sub(r"[^א-ת0-9]+", " ", value).strip()


def score(name: str, path: Path, text: str) -> int:
    wanted = normalize(name)
    stem = normalize(path.stem)
    body = normalize(text)
    tokens = [token for token in wanted.split() if len(token) > 1]
    points = sum(12 for token in tokens if token in stem)
    points += sum(2 for token in tokens if token in body)
    if wanted and wanted in stem:
        points += 100
    if wanted and wanted in body:
        points += 60
    return points


def main() -> None:
    documents = [(p, extract_docx(p)) for p in SOURCE.rglob("*.docx")]
    results = []
    for name in load_seed_dishes():
        ranked = sorted(
            ((score(name, path, text), path, text) for path, text in documents),
            key=lambda row: row[0],
            reverse=True,
        )
        best, second = ranked[0], ranked[1]
        results.append(
            {
                "dish": name,
                "score": best[0],
                "margin": best[0] - second[0],
                "source": str(best[1].relative_to(SOURCE)),
                "runner_up": str(second[1].relative_to(SOURCE)),
            }
        )
    output = SOURCE / "התאמת_מנות_למקורות.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print(json.dumps({"count": len(results), "low_score": sum(r["score"] < 40 for r in results), "low_margin": sum(r["margin"] < 10 for r in results)}, ensure_ascii=True))
    for result in results:
        if result["score"] < 40 or result["margin"] < 10:
            print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
