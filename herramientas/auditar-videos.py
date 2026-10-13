#!/usr/bin/env python3
"""Audita los IDs de YouTube que usa la página (const YTIDS en index.html).

Le pregunta a YouTube (oEmbed) el título y el canal de cada vídeo y avisa de los que
no parecen la canción pedida: otro artista, otro título, ensayos, fancams, directos...

    python3 herramientas/auditar-videos.py

Sólo lee; no cambia nada. Los «Topic» (audio oficial) y los canales del propio artista
son lo esperado; las subidas de letras de terceros salen con un aviso.
"""
import re, json, difflib, unicodedata, urllib.request, urllib.parse, concurrent.futures as cf
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / 'index.html').read_text(encoding='utf-8')
LIVE = dict(re.findall(r'"((?:[^"\\]|\\.)*)":"([\w-]{11})"', re.search(r'const YTIDS = \{(.*?)\n\};', HTML, re.S).group(1)))

def norm(x):
    x = unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode().lower()
    x = re.sub(r'\(.*?\)|\[.*?\]', ' ', x)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', x)).strip()

def oembed(vid):
    u = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + vid, safe='')
    for _ in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read().decode())
        except Exception as e:
            err = str(e)
    return {'err': err}

BAD = re.compile(r'dance practice|fancam|4k cam|\bcam\b|\blive\b|karaoke|cover|instrumental|sped|slowed|color coded|performance practice|comeback show|reaction|mashup|nightcore|8d', re.I)
with cf.ThreadPoolExecutor(8) as ex:
    res = dict(zip(LIVE, ex.map(lambda k: oembed(LIVE[k]), LIVE)))
bad = 0
for k, r in res.items():
    t, a = k.split('||'); arts = [norm(x) for x in re.split(r',|&', a) if norm(x)]
    if 'err' in r:
        bad += 1; print('ERROR', k, LIVE[k], r['err'][:50]); continue
    ti, au = norm(r['title']), norm(r['author_name'].replace(' - Topic', ''))
    t_ok = norm(t) in ti or difflib.SequenceMatcher(None, norm(t), ti).ratio() > .6 or ti in norm(t)
    a_ok = any(x in au or au in x or x in ti for x in arts) or any(difflib.SequenceMatcher(None, x, au).ratio() > .6 for x in arts)
    why = []
    if not t_ok: why.append('título distinto')
    if not a_ok: why.append('artista distinto')
    m = [w for w in BAD.findall(r['title']) if w.lower() not in t.lower()]
    if m: why.append('versión: ' + ','.join(m))
    if why:
        bad += 1; print(f"{k}\n   {LIVE[k]}  {r['title']!r} / {r['author_name']!r}   <- {'; '.join(why)}")
print(f"\n{bad} para revisar de {len(LIVE)}")
