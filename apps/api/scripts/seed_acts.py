"""
Скрипт завантаження 5 тестових актів законодавства (ТЗ v2, розділ 2, Tier 1).

Дані — публічно відомі публічні метадані актів України.
Тексти статтей — спрощені приклади для демонстрації структури.
У продакшені тексти завантажуються з data.rada.gov.ua / zakon.rada.gov.ua.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

from app.core.database import SessionLocal
from app.services.import_service import ImportService

FORCE_LEVELS = [
    (1, "Конституція України", "Найвищий рівень юридичної сили", 100),
    (2, "Міжнародні договори", "Договори, згоду на обов'язковість яких дала ВР", 90),
    (3, "Конституційні закони / Закони / Кодекси", "Закони та кодекси України", 80),
    (4, "Постанови Верховної Ради", "Постанови ВР", 70),
    (5, "Укази Президента", "Укази Президента України", 60),
    (6, "Постанови і розпорядження КМУ", "Кабінет Міністрів України", 50),
    (7, "Накази міністерств та ведомств", "Накази з державною реєстрацією", 40),
    (8, "Акти місцевих органів", "Акти громад, обладміністрацій", 30),
]

ACTS = [
    {
        "source_id": "constitution-ua-1996",
        "title": "Конституція України",
        "document_type": "Конституція",
        "document_number": "254к/96-ВР",
        "nreg": "254к/96-ВР",
        "adoption_date": date(1996, 6, 28),
        "issuing_authority": "Верховна Рада України",
        "legal_force_level": "constitution",
        "current_known_status": "Чинний",
        "source_url": "https://zakon.rada.gov.ua/laws/main/254к/96-вр",
        "source_metadata_json": {
            "adoption_date": "1996-06-28",
            "publication_date": "1996-06-28",
            "source": "zakon.rada.gov.ua",
        },
        "revisions": [
            {
                "revision_label": "Оригінальна редакція",
                "revision_date": date(1996, 6, 28),
                "effective_from": date(1996, 6, 28),
                "effective_to": None,
                "normalized_text": "Конституція України — Закон fundamentу…",
                "provisions": [
                    {
                        "provision_identifier": "Стаття 3",
                        "article_number": "3",
                        "heading": "Людина, її життя та здоров'я, гідність і честь",
                        "text": "Людина, її життя та здоров'я, гідність і честь є найвищою соціальною цінністю.",
                        "ordinal": 3,
                    },
                    {
                        "provision_identifier": "Стаття 53",
                        "article_number": "53",
                        "heading": "Дійне виконання обов'язків",
                        "text": "Особи, які не виконають обов'язків, передбачених Конституцією України та законами України, несуть юридичну відповідальність.",
                        "ordinal": 53,
                    },
                ],
            }
        ],
    },
    {
        "source_id": "civil-code-ua-2003",
        "title": "Цивільний кодекс України",
        "document_type": "Кодекс",
        "document_number": "435-IV",
        "nreg": "435-IV",
        "adoption_date": date(2003, 1, 16),
        "issuing_authority": "Верховна Рада України",
        "legal_force_level": "code",
        "current_known_status": "Чинний",
        "source_url": "https://zakon.rada.gov.ua/laws/main/435-15",
        "source_metadata_json": {
            "adoption_date": "2003-01-16",
            "source": "zakon.rada.gov.ua",
        },
        "revisions": [
            {
                "revision_label": "Оригінальна редакція",
                "revision_date": date(2003, 1, 16),
                "effective_from": date(2004, 1, 1),
                "effective_to": None,
                "normalized_text": "Цивільний кодекс України regulating цивільні відносини…",
                "provisions": [
                    {
                        "provision_identifier": "Стаття 6",
                        "article_number": "6",
                        "heading": "Цивільне законодавство",
                        "text": "Цивільні правові відносини регулюються Цивільним кодексом України та іншими актами законодавства, що відповідають йому.",
                        "ordinal": 6,
                    },
                    {
                        "provision_identifier": "Стаття 221",
                        "article_number": "221",
                        "heading": "Зобов'язання",
                        "text": "Зобов'язання виникають на підставі угоди сторін, чinu, що спричинив збиток, та інших підстав, передбачених законом.",
                        "ordinal": 221,
                    },
                ],
            }
        ],
    },
    {
        "source_id": "criminal-code-ua-2001",
        "title": "Кримінальний кодекс України",
        "document_type": "Кодекс",
        "document_number": "2341-III",
        "nreg": "2341-III",
        "adoption_date": date(2001, 4, 5),
        "issuing_authority": "Верховна Рада України",
        "legal_force_level": "code",
        "current_known_status": "Чинний",
        "source_url": "https://zakon.rada.gov.ua/laws/main/2341-14",
        "source_metadata_json": {
            "adoption_date": "2001-04-05",
            "source": "zakon.rada.gov.ua",
        },
        "revisions": [
            {
                "revision_label": "Оригінальна редакція",
                "revision_date": date(2001, 4, 5),
                "effective_from": date(2001, 9, 1),
                "effective_to": None,
                "normalized_text": "Кримінальний кодекс України — основний закон про кримінальну відповідальність…",
                "provisions": [
                    {
                        "provision_identifier": "Стаття 1",
                        "article_number": "1",
                        "heading": "Законодавство про кримінальну відповідальність",
                        "text": "Кримінальний кодекс встановлює кримінальну відповідальність за вчинки, заборонені законом під переслідуванням кримінального переслідування.",
                        "ordinal": 1,
                    },
                ],
            }
        ],
    },
    {
        "source_id": "kkoap-ua-2007",
        "title": "Кодекс України про адміністративні правопорушення",
        "document_type": "Кодекс",
        "document_number": "80731-10",
        "nreg": "80731-10",
        "adoption_date": date(2007, 12, 7),
        "issuing_authority": "Верховна Рада України",
        "legal_force_level": "code",
        "current_known_status": "Чинний",
        "source_url": "https://zakon.rada.gov.ua/laws/main/807-20",
        "source_metadata_json": {
            "adoption_date": "2007-12-07",
            "source": "zakon.rada.gov.ua",
        },
        "revisions": [
            {
                "revision_label": "Оригінальна редакція",
                "revision_date": date(2007, 12, 7),
                "effective_from": date(2008, 3, 1),
                "effective_to": None,
                "normalized_text": "Кодекс про адміністративні правопорушення regulating адміністративну відповідальність…",
                "provisions": [
                    {
                        "provision_identifier": "Стаття 5",
                        "article_number": "5",
                        "heading": "Адміністративне правопорушення",
                        "text": "Адміністративним правопорушенням є дія безчину, що порушує адміністративне законодавство.",
                        "ordinal": 5,
                    },
                ],
            }
        ],
    },
    {
        "source_id": "tax-code-ua-2010",
        "title": "Податковий кодекс України",
        "document_type": "Кодекс",
        "document_number": "2755-VI",
        "nreg": "2755-VI",
        "adoption_date": date(2010, 12, 2),
        "issuing_authority": "Верховна Рада України",
        "legal_force_level": "code",
        "current_known_status": "Чинний",
        "source_url": "https://zakon.rada.gov.ua/laws/main/2755-17",
        "source_metadata_json": {
            "adoption_date": "2010-12-02",
            "source": "zakon.rada.gov.ua",
        },
        "revisions": [
            {
                "revision_label": "Оригінальна редакція",
                "revision_date": date(2010, 12, 2),
                "effective_from": date(2011, 1, 1),
                "effective_to": None,
                "normalized_text": "Податковий кодекс України — основний закон про податки та збори…",
                "provisions": [
                    {
                        "provision_identifier": "Стаття 2",
                        "article_number": "2",
                        "heading": "Система податків і зборів",
                        "text": "Система податків і зборів включає податки і збори, встановлені цим Кодексом.",
                        "ordinal": 2,
                    },
                ],
            }
        ],
    },
]
def main() -> None:
    db = SessionLocal()
    try:
        with ImportService(db) as svc:
            # 1. Рівні юридичної сили
            for level, name, desc, weight in FORCE_LEVELS:
                svc.upsert_force_level(level=level, name=name, description=desc, priority_weight=weight)

            # 2. Акти з ревізіями та положеннями
            for act in ACTS:
                doc = svc.upsert_document(
                    source_id=act["source_id"],
                    title=act["title"],
                    document_type=act["document_type"],
                    document_number=act["document_number"],
                    nreg=act["nreg"],
                    adoption_date=act["adoption_date"],
                    issuing_authority=act["issuing_authority"],
                    legal_force_level=act["legal_force_level"],
                    current_known_status=act["current_known_status"],
                    source_url=act["source_url"],
                    source_metadata_json=act["source_metadata_json"],
                )

                for rev in act["revisions"]:
                    revision = svc.upsert_revision(
                        document=doc,
                        revision_label=rev["revision_label"],
                        revision_date=rev["revision_date"],
                        effective_from=rev["effective_from"],
                        effective_to=rev["effective_to"],
                        normalized_text=rev["normalized_text"],
                        source_url=act["source_url"],
                        verification_status="verified",
                    )

                    parent_provision = None
                    for prov in rev["provisions"]:
                        provision = svc.upsert_provision(
                            revision=revision,
                            provision_identifier=prov["provision_identifier"],
                            article_number=prov.get("article_number"),
                            heading=prov.get("heading"),
                            text=prov["text"],
                            ordinal=prov["ordinal"],
                            parent_provision_id=str(parent_provision.id) if parent_provision else None,
                        )
                        parent_provision = provision

            print(f"✅ Імпортовано актів: {len(ACTS)}")
            print(f"✅ Рівнів сили: {len(FORCE_LEVELS)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()