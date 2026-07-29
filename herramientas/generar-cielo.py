import json
stars=json.load(open('stars.6.json'))['features']
lines=json.load(open('constellations.lines.json'))['features']
cons=json.load(open('constellations.json'))['features']
dsos=json.load(open('dsos.bright.json'))['features']
names=json.load(open('starnames.json'))

# ── estrellas hasta magnitud 5.0 ──
S=[]
for f in stars:
    p=f['properties']; m=p.get('mag')
    if m is None or m>5.0: continue
    ra,dec=f['geometry']['coordinates'][:2]
    try: bv=float(p.get('bv') or 0)
    except: bv=0.0
    S.append([round(ra,2),round(dec,2),round(m,1),round(max(-0.4,min(2.0,bv)),2),f.get('id')])
S.sort(key=lambda r:r[2])
print('estrellas:',len(S))

# ── nombres propios de las más brillantes ──
NM={}
for hip,v in names.items():
    n=v.get('name') or ''
    if n: NM[str(hip)]=n
named=[]
for r in S[:110]:
    n=NM.get(str(r[4]))
    if n: named.append([r[0],r[1],r[2],round(max(-0.4,min(2.0,r[3])),2),n])
print('con nombre:',len(named))
out_stars=[[r[0],r[1],r[2],r[3]] for r in S]

# ── líneas de constelación ──
L=[]
for f in lines:
    segs=[]
    for seg in f['geometry']['coordinates']:
        segs.append([[round(c[0],1),round(c[1],1)] for c in seg])
    L.append([f['id'],segs])
print('constelaciones:',len(L))

# ── nombre y centro de cada constelación ──
C=[]
for f in cons:
    p=f.get('properties',{})
    n=p.get('name') or p.get('en') or f.get('id')
    g=f.get('geometry')
    if not g: continue
    c=g.get('coordinates')
    if g.get('type')=='Point' and c: C.append([f['id'],n,round(c[0],1),round(c[1],1)])
print('etiquetas:',len(C))

# ── objetos de cielo profundo con designación real ──
D=[]
TYPE={'gg':'galaxia','g':'galaxia','ga':'galaxia','gc':'cúmulo globular','oc':'cúmulo abierto',
      'pn':'nebulosa planetaria','dn':'nebulosa','bn':'nebulosa','sfr':'nebulosa','snr':'resto de supernova','en':'nebulosa'}
for f in dsos:
    p=f['properties']; m=p.get('mag')
    if m in (None,'') or float(m)>8.2: continue
    ra,dec=f['geometry']['coordinates'][:2]
    D.append([round(ra,2),round(dec,2),round(float(m),1),
              TYPE.get(p.get('type'),'objeto'),p.get('name') or p.get('desig'),p.get('desig')])
D.sort(key=lambda r:r[2])
D=D[:46]
print('objetos:',len(D))

js  = 'const SKY_STARS='+json.dumps(out_stars,separators=(',',':'))+';\n'
js += 'const SKY_NAMED='+json.dumps(named,ensure_ascii=False,separators=(',',':'))+';\n'
js += 'const SKY_LINES='+json.dumps(L,separators=(',',':'))+';\n'
js += 'const SKY_CONS='+json.dumps(C,ensure_ascii=False,separators=(',',':'))+';\n'
js += 'const SKY_DSO='+json.dumps(D,ensure_ascii=False,separators=(',',':'))+';\n'
open('sky.js','w').write(js)
print('KB:',len(js)//1024)
print('muestra nombres:',[n[4] for n in named[:12]])
print('muestra objetos:',[(d[4],d[5]) for d in D[:10]])
