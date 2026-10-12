#!/usr/bin/env python3
"""List all acts *in force* (status=Y) of the primary types on lex.uz (National Database of
Legislation of Uzbekistan) via its public search page, for Uzbek (Cyrillic, lang=3) and
Russian (lang=1). Output: _raw/uz/list.tsv  (lang, form, lex_id, badge, title)
"""
import os, re, sys, time, html, requests

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_raw', 'uz')
UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
FORMS = {'4131': 'constitution', '3964': 'code', '3968': 'law',
         '22216': 'kk-constitution', '22218': 'kk-law'}
LANGS = {'3': 'uz', '1': 'ru'}
ROW = re.compile(r'<a class="lx_link " href="/ru/docs/(-?\d+)"[^>]*>(.*?)</a>.*?badge-nine">(.*?)</span>', re.S)

def hidden(s):
    return {n: html.unescape(v) for n, v in re.findall(
        r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', s)}

def req(sess, method, url, **kw):
    for a in range(5):
        try:
            r = sess.request(method, url, timeout=120, **kw)
            if r.status_code == 200:
                return r.text
            print('HTTP', r.status_code, url, file=sys.stderr)
        except Exception as e:
            print('ERR', e, file=sys.stderr)
        time.sleep(10 * (a + 1))
    raise SystemExit('failed ' + url)

def main():
    os.makedirs(RAW, exist_ok=True)
    out = open(os.path.join(RAW, 'list.tsv'), 'w')
    for form, ftype in FORMS.items():
        for lcode, lang in LANGS.items():
            sess = requests.Session(); sess.headers['User-Agent'] = UA
            url = f'https://lex.uz/ru/search/nat?form_id={form}&status=Y&lang={lcode}'
            s = req(sess, 'GET', url)
            total = int((re.findall(r'найдено (\d+)', s) or ['0'])[0])
            seen = set(); page = 1
            while True:
                rows = ROW.findall(s)
                new = 0
                for lid, title, badge in rows:
                    if lid in seen: continue
                    seen.add(lid); new += 1
                    t = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', title))).strip()
                    b = re.sub(r'\s+', ' ', html.unescape(badge)).strip()
                    out.write(f'{lang}\t{ftype}\t{lid}\t{b}\t{t}\n')
                print(ftype, lang, 'page', page, 'rows', len(rows), 'total', len(seen), '/', total, flush=True)
                if len(seen) >= total or new == 0 or 'ucFoundActsControl$LinkButton1' not in s:
                    break
                data = hidden(s)
                data['__EVENTTARGET'] = 'ucFoundActsControl$LinkButton1'
                data['__EVENTARGUMENT'] = ''
                time.sleep(1.5)
                s = req(sess, 'POST', url, data=data)
                page += 1
            out.flush()
            time.sleep(2)

if __name__ == '__main__':
    main()
