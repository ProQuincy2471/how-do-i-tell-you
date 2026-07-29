import json, re, time, unicodedata, urllib.parse, urllib.request, difflib
import concurrent.futures as cf

ids = json.load(open('ids.json'))
UA = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36'}

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii','ignore').decode()
    s = s.lower()
    s = re.sub(r'\(.*?\)|\[.*?\]', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def sim(a,b): return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

def api(term, entity='song', limit=8):
    url = 'https://itunes.apple.com/search?' + urllib.parse.urlencode(
        {'term':term, 'entity':entity, 'limit':limit, 'media':'music'})
    for a in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
            return json.loads(r.read().decode('utf-8', 'ignore')).get('results', [])
        except Exception:
            time.sleep(1.2*(a+1))
    return []

BAD = re.compile(r'\b(karaoke|tribute|made popular|instrumental|cover version|in the style of)\b', re.I)

def best(results, title, artist):
    top, ts = None, 0
    for r in results:
        tn, an = r.get('trackName',''), r.get('artistName','')
        cn = r.get('collectionName','') or ''
        if BAD.search(an) or BAD.search(cn) or BAD.search(tn): continue
        if not r.get('artworkUrl100'): continue
        s = sim(tn, title)*0.62 + sim(an, artist)*0.38
        # bonus si el artista principal aparece dentro del nombre del artista
        if norm(artist.split(',')[0]) and norm(artist.split(',')[0]) in norm(an): s += 0.12
        if norm(title) and norm(title) in norm(tn): s += 0.06
        if s > ts: ts, top = s, r
    return top, ts

def art(r, px=600):
    u = r['artworkUrl100']
    return re.sub(r'/\d+x\d+bb\.(jpg|png)', f'/{px}x{px}bb.jpg', u)

def resolve(key):
    title, artist = key.split('||')[0], (key.split('||')[1] if '||' in key else '')
    a1 = artist.split(',')[0].strip()
    tries = [
        f'{title} {a1}',
        f'{norm(title)} {a1}',
        f'{title} {artist}',
        f'{norm(title)}',
    ]
    bestr, bests = None, 0
    for t in tries:
        if not t.strip(): continue
        res = api(t)
        r, s = best(res, title, artist)
        if r and s > bests: bestr, bests = r, s
        if bests >= 0.86: break
    if bestr and bests >= 0.55:
        return {'u': art(bestr), 'al': bestr.get('collectionName') or '', 'yr': (bestr.get('releaseDate') or '')[:4],
                'tn': bestr.get('trackName'), 'an': bestr.get('artistName'), 's': round(bests,3)}
    return None

keys = list(ids.keys())
out = {}
def work(k):
    try: return k, resolve(k)
    except Exception: return k, None

with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for i,(k,v) in enumerate(ex.map(work, keys)):
        out[k] = v
        if (i+1) % 25 == 0: print(i+1,'/',len(keys), flush=True)

miss = [k for k,v in out.items() if not v]
weak = [(k,v['s'],v['tn'],v['an']) for k,v in out.items() if v and v['s'] < 0.72]
print('sin portada:', len(miss))
for k in miss[:25]: print('  MISS', k)
print('dudosas:', len(weak))
for w in weak[:25]: print('  ?', w)
json.dump(out, open('covers.json','w'), ensure_ascii=False, indent=1)
