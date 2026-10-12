#!/usr/bin/env python3
"""Download the lex.uz document pages listed in _raw/uz/list.tsv (plus the constitutions)
into _raw/uz/html/<lex_id>.html.gz. Re-runs skip cached files."""
import gzip, os, sys, time, requests

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_raw', 'uz')
UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
EXTRA = [  # constitutions (the search result rows for them have no badge)
    ('uz', 'constitution', '6445145', '', 'Ўзбекистон Республикаси Конституцияси'),
    ('ru', 'constitution', '6445147', '', 'Конституция Республики Узбекистан'),
    ('uz', 'kk-constitution', '4953674', '', 'Қорақалпоғистон Республикасининг Конституцияси'),
]
DELAY = 1.5

def main():
    rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(RAW, 'list.tsv'))]
    rows = [tuple(r) for r in EXTRA] + [tuple(r) for r in rows]
    if len(sys.argv) > 1 and sys.argv[1] == 'reverse':   # run a 2nd worker from the other end
        rows = rows[::-1]
    os.makedirs(os.path.join(RAW, 'html'), exist_ok=True)
    s = requests.Session(); s.headers['User-Agent'] = UA
    for n, (lang, typ, lid, badge, title) in enumerate(rows):
        out = os.path.join(RAW, 'html', lid + '.html.gz')
        if os.path.exists(out) or os.path.exists(out + '.none'):
            continue
        url = f'https://lex.uz/{"ru/" if lang == "ru" else ""}docs/{lid}'
        for a in range(5):
            try:
                r = s.get(url, timeout=300)
                if r.status_code == 200 and 'ACT_' in r.text:
                    with gzip.open(out + '.tmp', 'wt', encoding='utf-8') as f:
                        f.write(r.text)
                    os.replace(out + '.tmp', out)
                    break
                print('HTTP', r.status_code, url, file=sys.stderr, flush=True)
                if r.status_code == 200:      # page without text (card only / PDF only)
                    open(out + '.none', 'w').close()
                    break
            except Exception as e:
                print('ERR', url, e, file=sys.stderr, flush=True)
            time.sleep(15 * (a + 1))
        time.sleep(DELAY)
        if n % 100 == 0:
            print('progress', n, len(rows), flush=True)
    print('done')

if __name__ == '__main__':
    main()
