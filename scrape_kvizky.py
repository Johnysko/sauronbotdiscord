"""Stáhne kvízové otázky z kviz.kvizky.cz (kategorie Film a seriály).

Licence webu: nekomerční šíření s odkazem na https://kviz.kvizky.cz
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

CATEGORY_URL = "https://kviz.kvizky.cz/kategorie.php?id=5&pg={page}"
SOURCE_URL = "https://kviz.kvizky.cz"
CATEGORY_NAME = "Film a seriály"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DISCORD_BUTTON_LABEL_MAX = 80


def truncate_label(text: str, limit: int = DISCORD_BUTTON_LABEL_MAX) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def class_list(attrs) -> list[str]:
    return dict(attrs).get("class", "").split()


class KvizkyParser(HTMLParser):
    """Parsuje otázky, 4 odpovědi a třídu .correct ze stránky kategorie."""

    def __init__(self) -> None:
        super().__init__()
        self.questions: list[dict] = []
        self._in_question = False
        self._question_depth = 0
        self._in_link = False
        self._in_answer = False
        self._in_note = False
        self._in_small = False
        self._answer_correct = False
        self._current: dict | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        classes = class_list(attrs)

        if (
            not self._in_question
            and tag == "div"
            and "question" in classes
            and "question-list" not in classes
        ):
            self._in_question = True
            self._question_depth = 1
            self._current = {
                "question": "",
                "options": [],
                "correct": None,
                "note": "",
            }
            return

        if not self._in_question:
            return

        if tag == "div":
            self._question_depth += 1

        if tag == "a" and "question-link" in classes:
            self._in_link = True
            self._buffer = []
            return

        if tag == "small" and self._in_link:
            self._in_small = True
            return

        if tag == "div" and "answer" in classes:
            self._in_answer = True
            self._answer_correct = "correct" in classes
            self._buffer = []
            return

        if tag == "div" and "note" in classes:
            self._in_note = True
            self._buffer = []

    def handle_endtag(self, tag) -> None:
        if tag == "small" and self._in_small:
            self._in_small = False
            return

        if tag == "a" and self._in_link:
            text = " ".join("".join(self._buffer).split())
            if self._current is not None:
                self._current["question"] = text
            self._in_link = False
            self._buffer = []
            return

        if tag != "div" or not self._in_question:
            return

        if self._in_answer:
            text = truncate_label(" ".join("".join(self._buffer).split()))
            if self._current is not None and text:
                self._current["options"].append(text)
                if self._answer_correct:
                    self._current["correct"] = text
            self._in_answer = False
            self._answer_correct = False
            self._buffer = []
            self._question_depth -= 1
            return

        if self._in_note:
            text = " ".join("".join(self._buffer).split())
            if self._current is not None:
                self._current["note"] = text
            self._in_note = False
            self._buffer = []
            self._question_depth -= 1
            return

        self._question_depth -= 1
        if self._question_depth <= 0:
            self._finish_question()

    def handle_data(self, data) -> None:
        if self._in_small:
            return
        if self._in_link or self._in_answer or self._in_note:
            self._buffer.append(data)

    def _finish_question(self) -> None:
        current = self._current
        self._in_question = False
        self._current = None
        if not current:
            return
        options = current["options"]
        correct = current["correct"]
        question = current["question"]
        if not question or len(options) != 4 or not correct or correct not in options:
            return
        self.questions.append(current)


def fetch_page(page: int) -> str:
    url = CATEGORY_URL.format(page=page)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8")


def scrape_questions(limit: int, pages: int) -> list[dict]:
    collected: list[dict] = []
    seen: set[str] = set()

    for page in range(1, pages + 1):
        html = fetch_page(page)
        parser = KvizkyParser()
        parser.feed(html)

        for item in parser.questions:
            key = item["question"]
            if key in seen:
                continue
            seen.add(key)
            collected.append(item)
            if len(collected) >= limit:
                return collected

    return collected


def main() -> int:
    parser = argparse.ArgumentParser(description="Stáhne filmové kvízové otázky z kvizky.cz")
    parser.add_argument("--limit", type=int, default=10, help="Kolik otázek uložit")
    parser.add_argument("--pages", type=int, default=1, help="Kolik stránek kategorie stáhnout")
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json"),
        help="Cílová JSON databáze",
    )
    args = parser.parse_args()

    try:
        questions = scrape_questions(args.limit, args.pages)
    except URLError as exc:
        print(f"Nepodařilo se stáhnout stránku: {exc}", file=sys.stderr)
        return 1

    payload = {
        "source": SOURCE_URL,
        "category": CATEGORY_NAME,
        "questions": [
            {
                "id": index,
                "question": item["question"],
                "options": item["options"],
                "correct": item["correct"],
                "note": item.get("note") or None,
            }
            for index, item in enumerate(questions, start=1)
        ],
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Uloženo {len(payload['questions'])} otázek do {args.output}")
    if len(payload["questions"]) < args.limit:
        print(
            f"Varování: požadováno {args.limit}, nalezeno jen {len(payload['questions'])}.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
