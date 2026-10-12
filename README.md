# Uzbekistan — legislation as Markdown (LawCodex)

Legislation of the Republic of Uzbekistan (Ўзбекистон Республикаси) as Markdown, in Uzbek
(`uz/`, state language, Cyrillic script as published in the national database) and Russian
(`ru/`). Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**.

## Coverage

__COUNTS__

All acts of the following types that the National Database of Legislation marks as **in force**
(status *Амалдаги / Действующий*), in their **current consolidated version**:

* the **Constitution** (new edition adopted by referendum on 30 April 2023);
* all **codes** (Civil Code parts I and II are separate documents);
* all **laws** (including constitutional laws and amending laws — ЎРҚ/ЗРУ numbers);
* the **Constitution of the Republic of Karakalpakstan** and the laws of Karakalpakstan in force
  that the database publishes (under `uz/qoraqalpogiston/` and `ru/karakalpakstan/`; some of these
  texts are in Karakalpak).

Amendment provenance notes of the database (e.g. "(… Қонуни таҳририда …)") are kept as block
quotes. LexUZ editorial commentaries and classifier indexes (hidden by default on the site) are
dropped. A handful of acts whose page shows no text (card or PDF only) are missing.

**Not covered:** presidential decrees and resolutions, government resolutions, ministerial and
agency acts, local acts, international treaties (tens of thousands of documents; available on
lex.uz). The Uzbek Latin-script and English versions offered by lex.uz are not included.

## Source

**Qonunchilik ma'lumotlari milliy bazasi / Национальная база данных законодательства Республики
Узбекистан — LEX.UZ** (https://lex.uz), operated by the "Adolat" National Legal Information Centre
under the Ministry of Justice. The list of acts comes from the site's search
(`/ru/search/nat?form_id=<type>&status=Y&lang=<3|1>`), the texts from the document pages
(`/docs/<id>` for Uzbek, `/ru/docs/<id>` for Russian). lex.uz has no `robots.txt` restrictions;
its published terms (privacy policy) do not restrict reuse. Requests were made sequentially with
pauses (at most two at a time).

Licence: under the Law of the Republic of Uzbekistan "On Copyright and Related Rights" (art. 8),
official documents — laws, decisions of courts and other texts of a legislative, administrative and
judicial nature, and their official translations — are not objects of copyright.

## Structure

```
uz/konstitutsiya/<slug>-<id>.md            Constitution
uz/kodekslar/<slug>-<id>.md                codes
uz/qonunlar/<year>/<number>-<id>.md        laws, by year of adoption (e.g. orq-1179-8514954.md)
uz/qoraqalpogiston/{konstitutsiya,qonunlar/<year>}/
ru/konstitutsiya/ ru/kodeksy/ ru/zakony/<year>/ ru/karakalpakstan/   the same in Russian
scripts/                                   fetch + convert code
```

`<id>` is the lex.uz document id (each language version has its own id), `<number>` the
transliterated act number (ЎРҚ-1179 → `orq-1179`, ЗРУ-1179 → `zru-1179`). Headings map the act
structure: part / section (бўлим, раздел) / chapter (боб, глава) / paragraph / article (модда,
статья).

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/uz_list.py      # -> ../_raw/uz/list.tsv
python3 scripts/uz_fetch.py     # -> ../_raw/uz/html/ (cached)
python3 scripts/uz_convert.py
```
