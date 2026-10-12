#!/usr/bin/env python3
"""Convert lex.uz document pages (_raw/uz/html/<lex_id>.html.gz, from uz_fetch.py) to Markdown.

Element classes used by lex.uz (div.<CLASS> inside #divCont):
  ACT_FORM / ACT_TITLE           act type and title
  TEXT_HEADER_DEFAULT            structural headings (section / chapter / paragraph ...)
  CLAUSE_DEFAULT                 article headings ("1-модда." / "Статья 1.")
  ACT_TEXT, BY_DEFAULT, ...      body text
  CHANGES_ORIGINS, FOOTNOTE      amendment provenance notes (kept as block quotes)
  COMMENT, INDEXES_ON_REF        LexUZ editorial comments / classifier indexes (hidden on site; dropped)
"""
import gzip, os, re, sys, html
from bs4 import BeautifulSoup, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
RAW = os.path.abspath(os.path.join(REPO, '..', '_raw', 'uz'))
RETRIEVED = '2026-10-12'

DIRS = {
    'uz': {'constitution': 'konstitutsiya', 'code': 'kodekslar', 'law': 'qonunlar',
           'kk-constitution': 'qoraqalpogiston/konstitutsiya', 'kk-law': 'qoraqalpogiston/qonunlar'},
    'ru': {'constitution': 'konstitutsiya', 'code': 'kodeksy', 'law': 'zakony',
           'kk-constitution': 'karakalpakstan/konstitutsiya', 'kk-law': 'karakalpakstan/zakony'},
}
TYPE_FM = {'constitution': 'constitution', 'code': 'code', 'law': 'act',
           'kk-constitution': 'constitution', 'kk-law': 'act'}

KINDS = ['part', 'section', 'subsection', 'chapter', 'paragraph', 'article']
PATTERNS = {
    'part': re.compile(r'^((общая|особенная)\s+часть|часть\s+[\dIVXLC]+|(умумий|махсус)\s+қисм|[\dIVXLC]+[-‑\s]*қисм\b)', re.I),
    'section': re.compile(r'^(раздел\b|[\dIVXLC]+(-\d+)?[-‑\s]*бўлим\b|.{0,25}\bбўлим\b|бўлим\s)', re.I),
    'subsection': re.compile(r'^(подраздел\b|[\dIVXLC]+[-‑\s]*кичик\s+бўлим)', re.I),
    'chapter': re.compile(r'^(глава\s|[\dIVXLC]+(\d|-)*[-‑\s]*боб\b|боб\s)', re.I),
    'paragraph': re.compile(r'^(параграф\s|§\s*\d|[\dIVXLC]+(-\d+)?[-‑\s]*параграф\b)', re.I),
    'article': re.compile(r'^(статья\s+\d|\d+(\d|-)*[-‑\s]*модда\b|модда\s+\d)', re.I),
}


def kind_of(t):
    t = t.strip()
    for k in KINDS:
        if PATTERNS[k].match(t):
            return k
    return None


def clean(t):
    t = t.replace('\xa0', ' ')
    t = re.sub(r'[ \t\r\f\v]+', ' ', t)
    t = re.sub(r' *\n *', '\n', t)
    return t.strip()


def md_escape(t):
    t = re.sub(r'^(#+)', r'\\\1', t)
    t = re.sub(r'^(\d+)([.)]) ', r'\1\\\2 ', t)
    t = re.sub(r'^([-+*>]) ', r'\\\1 ', t)
    return t


def text_of(node):
    out = []
    for d in node.descendants:
        if isinstance(d, NavigableString):
            if d.parent.name in ('script', 'style'):
                continue
            out.append(str(d))
        elif d.name == 'br':
            out.append('\n')
        elif d.name in ('p', 'div') and out and not out[-1].endswith('\n'):
            out.append('\n')
    return ''.join(out)


def table_md(tbl):
    rows = []
    for tr in tbl.find_all('tr'):
        cells = [clean(text_of(td)).replace('\n', '<br>').replace('|', '\\|') for td in tr.find_all(['td', 'th'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    if tbl.find(attrs={'colspan': True}) or tbl.find(attrs={'rowspan': True}):
        out = ['<table>']
        for tr in tbl.find_all('tr'):
            out.append('<tr>' + ''.join(
                '<td%s%s>%s</td>' % (
                    f' colspan="{td["colspan"]}"' if td.get('colspan') else '',
                    f' rowspan="{td["rowspan"]}"' if td.get('rowspan') else '',
                    html.escape(clean(text_of(td))).replace('\n', '<br>'))
                for td in tr.find_all(['td', 'th'])) + '</tr>')
        out.append('</table>')
        return '\n'.join(out)
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    out = ['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * n]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(out)


SKIP = {'COMMENT', 'INDEXES_ON_REF', 'COMMENTLEXUZ', 'UNOFFIAL'}
NOTE = {'CHANGES_ORIGINS', 'FOOTNOTE', 'PUBLICATION_ORIGIN', 'NEW_EDITION', 'OFFICIAL_SOUR_TEXT'}


def convert(soup):
    cont = soup.find(id='divCont')
    if cont is None:
        return None, None, []
    form = title = None
    blocks = []
    for el in cont.find_all('div', recursive=False):
        cls = [c for c in (el.get('class') or []) if c.isupper()]
        if not cls:
            continue
        c = cls[0]
        if c in SKIP:
            continue
        for x in el.select('.lx_elem2'):
            x.decompose()
        tables = el.find_all('table')
        tmd = []
        for t in tables:
            tmd.append(table_md(t))
            t.extract()
        txt = clean(text_of(el))
        if c == 'ACT_FORM':
            form = txt or form
            continue
        if c == 'ACT_TITLE' and title is None:
            title = re.sub(r'\s+', ' ', txt)
            continue
        if txt:
            if c in NOTE:
                blocks.append(('note', txt))
            elif c == 'CLAUSE_DEFAULT':
                blocks.append(('h', 'article', re.sub(r'\s+', ' ', txt)))
            elif c in ('TEXT_HEADER_DEFAULT', 'ACT_TITLE_APPL', 'TEXT_BOLD_CENTER'):
                k = kind_of(txt)
                blocks.append(('h', k, re.sub(r'\s+', ' ', txt)))
            else:
                for ln in txt.split('\n'):
                    if ln.strip():
                        blocks.append(('p', ln.strip()))
        for m in tmd:
            if m:
                blocks.append(('raw', m))
    return form, title, blocks


def render(blocks):
    present = [k for k in KINDS if any(b[0] == 'h' and b[1] == k for b in blocks)]
    level = {k: min(2 + i, 6) for i, k in enumerate(present)}
    out = []
    for b in blocks:
        if b[0] == 'h':
            k, t = b[1], b[2]
            out.append(f'**{t}**' if k is None else '#' * level[k] + ' ' + t)
        elif b[0] == 'p':
            out.append(md_escape(b[1]))
        elif b[0] == 'note':
            out.append('> ' + b[1].replace('\n', '\n> '))
        else:
            out.append(b[1])
    return '\n\n'.join(out) + '\n'


def yq(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


TRANS = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ',
                 ['a', 'b', 'v', 'g', 'd', 'e', 'yo', 'j', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's',
                  't', 'u', 'f', 'x', 'ts', 'ch', 'sh', 'sh', '', 'i', '', 'e', 'yu', 'ya', 'o', 'q', 'g', 'h']))


TRANS.update({'ө': 'o', 'ү': 'u', 'ң': 'n', 'ә': 'a', 'і': 'i', 'ı': 'i', 'ʻ': '', 'ʼ': ''})


def slug(s):
    s = ''.join(TRANS.get(ch, ch) for ch in s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60]


def main():
    rows = []
    sys.path.insert(0, HERE)
    from uz_fetch import EXTRA
    rows = [tuple(r) for r in EXTRA] + [tuple(l.rstrip('\n').split('\t')) for l in open(os.path.join(RAW, 'list.tsv'))]
    stats = {}
    missing = 0
    seen = set()
    for lang, typ, lid, badge, ltitle in rows:
        if lid in seen:
            continue
        seen.add(lid)
        fn = os.path.join(RAW, 'html', lid + '.html.gz')
        if not os.path.exists(fn):
            missing += 1
            continue
        s = gzip.open(fn, 'rt', encoding='utf-8').read()
        soup = BeautifulSoup(s, 'lxml')
        form, title, blocks = convert(soup)
        if not blocks:
            missing += 1
            print('no text', lid, file=sys.stderr)
            continue
        title = title or ltitle
        m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', badge)
        date = f'{m.group(3)}-{m.group(2)}-{m.group(1)}' if m else None
        if not date:
            m = re.search(r'(\d{4}) йил (\d{1,2}) ', badge)
        num = None
        m2 = re.search(r'(?:№\s*|йилдаги\s+)([^\s,]+?)(?:-сон)?$', badge)
        if m2:
            num = m2.group(1)
        year = date[:4] if date else 'unknown'
        sub = DIRS[lang][typ]
        if typ in ('law', 'kk-law'):
            name = (slug(num) + '-' if num else '') + lid
        else:
            name = slug(re.sub(r'(?i)^(ўзбекистон республикасининг|ўзбекистон республикаси|қорақалпоғистон республикасининг)\s+', '', title)) + '-' + lid
        if typ in ('law', 'kk-law'):
            rel = os.path.join(lang, sub, year, name + '.md')
        else:
            rel = os.path.join(lang, sub, name + '.md')
        url = f'https://lex.uz/{"ru/" if lang == "ru" else ""}docs/{lid}'
        fm = ['---', f'title: {yq(title)}', f'identifier: "lex.uz:{lid}"']
        if num:
            fm.append(f'number: {yq(num)}')
        fm += [f'type: {TYPE_FM[typ]}', 'jurisdiction: uz', f'language: {lang}']
        if lang == 'uz':
            fm.append('script: Cyrl')
        if date:
            fm.append(f'date: {date}')
        fm += ['status: in_force']
        if badge:
            fm.append(f'citation: {yq(badge)}')
        fm += [f'source: "{url}"', f'retrieved: {RETRIEVED}', '---', '']
        md = '\n'.join(fm) + f'\n# {title}\n\n' + render(blocks)
        out = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(md)
        stats[(lang, typ)] = stats.get((lang, typ), 0) + 1
    print(stats, 'missing', missing)


if __name__ == '__main__':
    main()
