import json, io, os, urllib.request, colorsys, concurrent.futures as cf
from PIL import Image

ids = json.load(open('ids.json'))
UA = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36'}
os.makedirs('thumbs', exist_ok=True)

def fetch(vid):
    p = f'thumbs/{vid}.jpg'
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        return open(p,'rb').read()
    for url in (f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg',
                f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'):
        try:
            d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
            if len(d) > 2000:
                open(p,'wb').write(d); return d
        except Exception: pass
    return None

def hexs(r,g,b): return '#%02x%02x%02x' % (int(r),int(g),int(b))
def mk(h,l,s):
    r,g,b = colorsys.hls_to_rgb(h % 1.0, max(0,min(1,l)), max(0,min(1,s)))
    return hexs(r*255,g*255,b*255)

def pal(vid):
    d = fetch(vid)
    if not d: return None
    im = Image.open(io.BytesIO(d)).convert('RGB')
    w,h = im.size
    if abs(w/h - 4/3) < 0.05:                    # hqdefault lleva barras
        im = im.crop((0, int(h*0.12), w, int(h*0.88)))
    im = im.resize((64,36))
    q = im.quantize(colors=10, method=Image.MEDIANCUT).convert('RGB')
    cols = q.getcolors(64*36)
    tot = sum(c[0] for c in cols)
    cand = []
    for cnt,(r,g,b) in cols:
        hh,ll,ss = colorsys.rgb_to_hls(r/255,g/255,b/255)
        if ll < 0.06 or ll > 0.95: continue
        weight = cnt/tot
        score = (ss**2.2)*3.0 + weight*0.9 - abs(ll-0.5)*0.55
        cand.append((score, hh, ll, ss, weight))
    if not cand: return None
    cand.sort(key=lambda t: -t[0])
    _, h1, l1, s1, w1 = cand[0]
    # segundo tono realmente distinto
    h2, s2 = h1, s1
    for _, hh, ll, ss, ww in cand[1:]:
        dh = abs(hh-h1); dh = min(dh, 1-dh)
        if dh > 0.07:
            h2, s2 = hh, ss; break
    else:
        h2 = (h1 + 0.09) % 1.0; s2 = s1
    # tono medio ponderado para el fondo
    hb = h1
    A = max(0.52, min(0.92, s1*1.55 + 0.18))
    B = max(0.45, min(0.88, s2*1.45 + 0.16))
    return {
        'a': mk(h1, 0.645, A),   # acento
        'b': mk(h2, 0.585, B),   # secundario
        'd': mk(hb, 0.075, min(0.55, A*0.55)),   # fondo profundo
        'm': mk(hb, 0.175, min(0.50, A*0.50)),   # medio
        'h': round(h1*360),
    }

keys = list(ids.keys())
out = {}
def work(k):
    v = ids[k]
    try: return k, (pal(v) if v else None)
    except Exception: return k, None

with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for i,(k,p) in enumerate(ex.map(work, keys)):
        out[k] = p
        if (i+1) % 40 == 0: print(i+1,'/',len(keys), flush=True)

miss = [k for k,v in out.items() if not v]
print('missing:', len(miss), miss[:8])
json.dump(out, open('palettes.json','w'), indent=1)
for k in ['PLAYING WITH FIRE||BLACKPINK','What is Love?||TWICE','Euphoria||BTS','soft spot||keshi','Ojitos Lindos||Bad Bunny, Bomba Estéreo']:
    print(k.split('||')[0][:22].ljust(24), out.get(k))
