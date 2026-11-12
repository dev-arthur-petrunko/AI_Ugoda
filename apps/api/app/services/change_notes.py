"""§4.3: парсинг офіційних приміток про зміни в текстах актів.

Примітки у фігурних дужках на zakon.rada.gov.ua — офіційні факти джерела:
{Статтю 65 доповнено частиною одинадцятою згідно із Законом № 3587-IX від 22.02.2024}
{Статтю 186 - 2 виключено на підставі Закону № 3504-IV від 23.02.2006}
{Частина третя статті 65 в редакції Законів № 1405-VIII від 02.06.2016, № 3587-IX від 22.02.2024}

З них будуються legal_links (хто кого змінив) і legal_events (стрічка «Нові зміни»).

Правило «не вигадувати»: розбираємо лише явні формулювання; те, що не вдалося
розібрати, не зберігається як факт (без здогадок).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Примітки джерела: { … } — без вкладених дужок.
NOTE_RE = re.compile(r"\{([^{}]{5,1000})\}")

# Посилання на акт-джерело: «№ 3587-IX від 22.02.2024», «№ 55/97-ВР від 07.02.97».
ACT_REF_RE = re.compile(
    r"№\s*(\d+(?:/\d+)?\s*-\s*[0-9A-Za-zА-Яа-яЇїЄєІіІІ]+)\s+від\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
    re.IGNORECASE,
)

# Номер статті, якої стосується примітка: «статті 64 - 1», «Статтю 186 - 2».
ARTICLE_REF_RE = re.compile(
    r"статт[яюі](?:\s+у)?\s+(\d+(?:\s*-\s*\d+)?)",
    re.IGNORECASE,
)

# Дія визначається ключовим словом формулювання (порядок важливий:
# спершу найспецифічніші, бо «виключено» теж містить «виключен…»).
_ACTION_MARKERS: list[tuple[str, str]] = [
    ("excludes", "виключен"),           # «виключено на підставі Закону…»
    ("adds", "доповнен"),               # «доповнено частиною… / статтею…»
    ("repeals", "чинність"),            # «втратив чинність»
    ("replaces", "редакції"),           # «в редакції Закону…»
    ("amends", "змін"),                 # «із змінами, внесеними згідно із Законом…»
    ("amends", "внесено зміни"),
]


def _norm_article(raw: str) -> str:
    """«64 - 1» → «64-1»."""
    return re.sub(r"\s*-\s*", "-", raw.strip())


def _norm_date(raw: str) -> str | None:
    """15.07.2021 → 2021-07-15; 07.02.97 → 1997-02-07 (двозначний рік)."""
    parts = raw.split(".")
    if len(parts) != 3:
        return None
    dd, mm, yy = parts
    try:
        dd_i, mm_i, yy_i = int(dd), int(mm), int(yy)
    except ValueError:
        return None
    if yy_i < 100:
        yy_i += 1900 if yy_i >= 30 else 2000
    if not (1 <= mm_i <= 12 and 1 <= dd_i <= 31):
        return None
    return f"{yy_i:04d}-{mm_i:02d}-{dd_i:02d}"


def _norm_act_number(raw: str) -> str:
    """«3587 - IX» / «3587-IX» → «3587-IX»; пробіли навколо «/» прибираємо."""
    s = re.sub(r"\s*-\s*", "-", raw.strip())
    s = re.sub(r"\s*/\s*", "/", s)
    return s.upper()


@dataclass
class ChangeNote:
    """Одна розпізнана примітка-факт про зміну."""

    action: str                 # amends | adds | excludes | replaces | repeals
    act_number: str             # «3587-IX» (нормалізований, для зіставлення з nreg)
    act_date: str | None        # «2024-02-22» (ISO) або None, якщо не розібрано
    article: str | None         # стаття, якої стосується примітка («65», «186-2»)
    evidence: str               # фрагмент тексту-джерела (доказ)
    link_type: str = field(init=False)
    event_type: str = field(init=False)

    def __post_init__(self) -> None:
        # Мапінг дії → тип зв'язку (дозволені моделлю LegalLink).
        mapping = {
            "amends": "amends",
            "adds": "amends",
            "excludes": "repeals",
            "replaces": "amends",
            "repeals": "repeals",
        }
        self.link_type = mapping.get(self.action, "refers_to")
        self.event_type = self.action


def _classify_action(note: str) -> str | None:
    """Визначає дію за ключовим словом формулювання; None — не розпізнано."""
    low = note.lower()
    for action, marker in _ACTION_MARKERS:
        if marker in low:
            return action
    return None


def extract_change_notes(text: str) -> list[ChangeNote]:
    """Витягує з тексту положення примітки-факти про зміни.

    Повертає лише явно розпізнані формулювання (дія + акт-джерело);
    решта приміток ігнорується — не вгадуємо.
    """
    notes: list[ChangeNote] = []
    if not text:
        return notes

    for note_match in NOTE_RE.finditer(text):
        note = note_match.group(1)

        action = _classify_action(note)
        if action is None:
            continue

        acts = ACT_REF_RE.findall(note)
        if not acts:
            # Примітка без акта-джерела не є фактом «хто змінив».
            continue

        art_match = ARTICLE_REF_RE.search(note)
        article = _norm_article(art_match.group(1)) if art_match else None

        evidence = "{" + note.strip() + "}"
        seen: set[tuple[str, str | None]] = set()
        for act_number_raw, act_date_raw in acts:
            act_number = _norm_act_number(act_number_raw)
            act_date = _norm_date(act_date_raw)
            key = (act_number, act_date)
            if key in seen:
                continue
            seen.add(key)
            notes.append(
                ChangeNote(
                    action=action,
                    act_number=act_number,
                    act_date=act_date,
                    article=article,
                    evidence=evidence[:500],
                )
            )
    return notes
