# -*- coding: utf-8 -*-
"""§4.3: офіційні примітки про зміни → факти (без вигадоків)."""

from app.services.change_notes import extract_change_notes


def test_amends_note_with_act_number_and_date():
    text = (
        "Стаття 65. Призначення пенсії. "
        "{Частину третю статті 65 доповнено абзацом другим згідно із Законом "
        "№ 1667-IX від 15.07.2021}"
    )
    notes = extract_change_notes(text)
    assert len(notes) == 1
    n = notes[0]
    assert n.action == "adds"
    assert n.act_number == "1667-IX"
    assert n.act_date == "2021-07-15"
    assert n.article == "65"
    assert n.link_type == "amends"
    assert n.evidence.startswith("{")


def test_multiple_acts_in_one_note():
    text = (
        "{Частина третя статті 65 в редакції Законів № 1405-VIII від 02.06.2016 , "
        "№ 3587-IX від 22.02.2024}"
    )
    notes = extract_change_notes(text)
    assert len(notes) == 2
    assert {n.act_number for n in notes} == {"1405-VIII", "3587-IX"}
    assert all(n.action == "replaces" for n in notes)


def test_excluded_note_is_repeal():
    text = "{Статтю 186 - 2 виключено на підставі Закону № 3504-IV від 23.02.2006}"
    notes = extract_change_notes(text)
    assert len(notes) == 1
    assert notes[0].action == "excludes"
    assert notes[0].link_type == "repeals"
    assert notes[0].article == "186-2"


def test_two_digit_year_normalized():
    text = "{Стаття 186 із змінами, внесеними згідно із Законом № 55/97-ВР від 07.02.97}"
    notes = extract_change_notes(text)
    assert len(notes) == 1
    assert notes[0].act_number == "55/97-ВР"
    assert notes[0].act_date == "1997-02-07"


def test_note_without_act_is_ignored():
    """Примітка без акта-джерела не є фактом «хто змінив» — не вгадуємо."""
    text = "{Статтю доповнено новою частиною згідно із Змінами}"
    assert extract_change_notes(text) == []


def test_text_without_notes_is_empty():
    assert extract_change_notes("Просто текст статті без приміток.") == []
    assert extract_change_notes("") == []


def test_unrecognized_note_is_ignored():
    text = "{Дивись також розділ про адміністративну процедуру}"
    assert extract_change_notes(text) == []
