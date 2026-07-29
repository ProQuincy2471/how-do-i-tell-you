/* ─────────────────────────────────────────────────────────────────────────
   resolve4 — los 190 vídeos, sólo de fuentes oficiales.

   YouTube Music etiqueta cada resultado con musicVideoType:
     OMV = vídeo musical oficial del artista
     ATV = pista de audio oficial  (lo que sirve el canal "<Artista> - Topic")
     UGC = subida de usuario: covers, fancams, letras traducidas, karaoke…
   Nos quedamos con OMV cuando existe y de verdad es la canción; si no, ATV.
   Nunca UGC. La duración de iTunes arbitra, y al final se comprueba que
   cada vídeo elegido se pueda reproducir incrustado.
   ───────────────────────────────────────────────────────────────────────── */
const fs=require('fs');
const path=require('path');
// la raíz del proyecto: este script vive en herramientas/
const DIR=path.resolve(__dirname,'..');
const DATOS=path.join(__dirname,'datos');
const html=fs.readFileSync(DIR+'/index.html','utf8');
const ACTS=eval(html.match(/const ACTS ?= ?(\[[\s\S]*?\n\];)/)[1].replace(/;$/,''));
const songs=[];const seen=new Set();
ACTS.forEach(a=>a.songs.forEach(([t,ar])=>{
  const k=t+'||'+ar; if(seen.has(k))return; seen.add(k); songs.push({t,ar,key:k});
}));
if(process.env.ONLY){ const o=JSON.parse(process.env.ONLY);
  const keep=songs.filter(s=>o.includes(s.key)); songs.length=0; songs.push(...keep); }
else if(process.env.LIMIT) songs.length=+process.env.LIMIT;
console.error('canciones:',songs.length);

const KEY='AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30';
const CTX={client:{clientName:'WEB_REMIX',clientVersion:'1.20240401.01.00',hl:'en',gl:'US'}};
const P={songs:'EgWKAQIIAWoKEAkQBRAKEAMQBA==', videos:'EgWKAQIQAWoKEAkQBRAKEAMQBA=='};
const UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

const strip=s=>(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')
  .replace(/[’'`´]/g,'').replace(/&/g,' and ')
  .replace(/[^a-z0-9]+/g,' ').trim();
function shape(t,arts){
  let x=' '+strip(t)+' ';
  arts.forEach(a=>{ if(a.length>2) x=x.split(' '+a+' ').join(' '); });
  x=x.replace(/\b(official|music|video|audio|visuali[sz]er|lyric|lyrics|mv|hd|hq|4k|explicit|clip|feat|ft|featuring|with|prod)\b/g,' ');
  return x.replace(/\s+/g,' ').trim();
}
function sim(a,b){
  a=strip(a);b=strip(b); if(!a||!b)return 0; if(a===b)return 1;
  const bg=s=>{const o=new Set();for(let i=0;i<s.length-1;i++)o.add(s.slice(i,i+2));return o;};
  const A=bg(a),B=bg(b);let n=0;A.forEach(x=>{if(B.has(x))n++;});
  return 2*n/(A.size+B.size);
}
const artistList=ar=>ar.split(/,|&| x |\bft\.?\b|\bfeat\.?\b/i).map(s=>s.trim()).filter(Boolean);
const parseLen=t=>{const p=(t||'').trim().split(':').map(Number);
  return p.some(isNaN)?0:p.reduce((a,b)=>a*60+b,0);};
function parseViews(s){
  const m=(s||'').match(/([\d.,]+)\s*([KMB])?/); if(!m)return 0;
  const n=parseFloat(m[1].replace(/,/g,''));
  return n*({K:1e3,M:1e6,B:1e9}[m[2]]||1);
}

async function ytm(query,params){
  for(let a=0;a<5;a++){
    try{
      const r=await fetch('https://music.youtube.com/youtubei/v1/search?key='+KEY,{
        method:'POST',
        headers:{'Content-Type':'application/json','Origin':'https://music.youtube.com','User-Agent':UA},
        body:JSON.stringify({context:CTX,query,params})});
      if(!r.ok){ await sleep(700*(a+1)); continue; }
      const j=await r.json();
      const raw=[];(function w(o){ if(!o||typeof o!=='object')return;
        if(Array.isArray(o))return o.forEach(w);
        if(o.musicResponsiveListItemRenderer)raw.push(o.musicResponsiveListItemRenderer);
        for(const k in o)w(o[k]); })(j);
      return raw.map(it=>{
        const cols=(it.flexColumns||[]).map(c=>
          ((c.musicResponsiveListItemFlexColumnRenderer.text.runs)||[]).map(r=>r.text));
        const sub=(cols[1]||[]).filter(x=>x!==' • ');
        const js=JSON.stringify(it);
        return { id:(it.playlistItemData&&it.playlistItemData.videoId)||null,
          type:(js.match(/"musicVideoType":"MUSIC_VIDEO_TYPE_([A-Z_]+)"/)||[])[1]||'',
          title:(cols[0]||[]).join(''), by:sub[0]||'',
          album:sub.length>2?sub[1]:'',
          len:parseLen(sub.find(x=>/^\d+:\d\d(:\d\d)?$/.test(x))||''),
          views:parseViews(sub.find(x=>/plays|views/.test(x))) };
      }).filter(v=>v.id&&v.len>0);
    }catch(e){ await sleep(700*(a+1)); }
  }
  return [];
}

async function itunes(t,ar){
  const a1=artistList(ar)[0];
  for(let a=0;a<3;a++){
    try{
      const r=await fetch('https://itunes.apple.com/search?media=music&entity=song&limit=15&term='
        +encodeURIComponent(t+' '+a1));
      const j=await r.json();
      let best=null,bs=0;
      (j.results||[]).forEach(x=>{
        const s=sim(x.trackName,t)*0.66+sim(x.artistName,a1)*0.34;
        if(s>bs){bs=s;best=x;}
      });
      if(best&&bs>0.5)return{sec:Math.round(best.trackTimeMillis/1000),name:best.trackName,art:best.artistName};
    }catch(e){ await sleep(400*(a+1)); }
  }
  return null;
}

/* ¿el vídeo existe y es público?  (oembed responde 200 sólo entonces;
   400/401/403 = borrado, privado o con la inserción bloqueada) */
async function embeddable(id){
  for(let a=0;a<3;a++){
    try{
      const r=await fetch('https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v='+id,
        {headers:{'User-Agent':UA}});
      if(r.status===429){ await sleep(1500*(a+1)); continue; }
      return {ok:r.status===200, st:String(r.status)};
    }catch(e){ await sleep(500*(a+1)); }
  }
  return {ok:false,st:'error'};
}

function scoreTrack(v,s,arts,ref){
  const wantRemix=/remix/i.test(s.t), hasRemix=/remix/i.test(v.title);
  const ts=sim(shape(v.title,arts),shape(s.t,arts));
  const as=Math.max(...arts.map(a=>sim(v.by,a)),0);
  let sc=ts*100+as*55, why=[];
  if(shape(v.title,arts)===shape(s.t,arts)){ sc+=45; why.push('título exacto'); }
  if(wantRemix!==hasRemix){ sc-=75; why.push('remix no coincide'); }
  // versiones que no pedimos
  if(!/japanese|korean|spanish|acoustic|live|sped|slowed/i.test(s.t)
     && /\b(japanese|korean|chinese|spanish|acoustic|live|sped up|slowed|instrumental|a cappella|demo|edit)\b/i.test(v.title)){
    sc-=80; why.push('versión distinta'); }
  if(ref&&ref.sec){
    const d=v.len-ref.sec, ad=Math.abs(d);
    if(ad<=4) sc+=55; else if(ad<=12) sc+=38; else if(ad<=30) sc+=12;
    else if(ad<=60) sc-=30; else sc-=130;
    why.push('Δ'+d+'s');
  }
  return {sc,why:why.join(', '),ts,as};
}

(async()=>{
  const out={}, rep=[];
  let i=0, done=0;
  await Promise.all(Array.from({length:5},async()=>{
    while(i<songs.length){
      const s=songs[i++];
      const arts=artistList(s.ar).map(strip);
      const q=artistList(s.ar)[0]+' '+s.t;
      const ref=await itunes(s.t,s.ar);
      const [tr,vi]=await Promise.all([ytm(q,P.songs),ytm(q,P.videos)]);

      // ── pista oficial (ATV) ──
      const tracks=tr.filter(v=>v.type==='ATV')
        .map(v=>({v,...scoreTrack(v,s,arts,ref)})).sort((a,b)=>b.sc-a.sc);
      const track=tracks[0]&&tracks[0].sc>105?tracks[0]:null;
      const base=ref&&ref.sec?ref.sec:(track?track.v.len:0);

      // ── vídeo oficial (OMV) del propio artista, el más visto ──
      const omv=vi.filter(v=>v.type==='OMV')
        .filter(v=>Math.max(...arts.map(a=>sim(v.by,a)),0)>0.62)
        .filter(v=>shape(v.title,arts)===shape(s.t,arts))
        .sort((a,b)=>b.views-a.views);
      // el vídeo canónico es el más visto; si ése no es la canción (corto,
      // versión de directo, montaje) preferimos el audio oficial antes que
      // un vídeo secundario del mismo artista
      const vidLong=omv.length?omv[0]:null;
      const vid=(vidLong&&base&&vidLong.len>=base-15&&vidLong.len<=base+40)?vidLong:null;

      const pickV=vid?{id:vid.id,src:'vídeo oficial',v:vid}:null;
      const pickT=track?{id:track.v.id,src:'audio oficial (Topic)',v:track.v,why:track.why}:null;
      const pick=pickV||pickT||(tracks[0]?{id:tracks[0].v.id,src:'pista dudosa',v:tracks[0].v,why:tracks[0].why}:null);

      let emb={ok:true,st:'—'};
      if(pick) emb=await embeddable(pick.id);
      // si el vídeo no se puede incrustar, caemos al audio oficial
      let note='';
      if(pick&&!emb.ok&&pickV&&pickT){
        const e2=await embeddable(pickT.id);
        if(e2.ok){ note='vídeo no incrustable → audio oficial'; pick.id=pickT.id; pick.src=pickT.src; pick.v=pickT.v; emb=e2; }
      }
      if(vidLong&&!vid) note=(note?note+'; ':'')+`vídeo oficial descartado por duración (${vidLong.len}s vs ${base}s)`;

      out[s.key]=pick?pick.id:null;
      rep.push({key:s.key, id:pick?pick.id:null, src:pick?pick.src:'sin resultado',
        ti:pick?pick.v.title:'', by:pick?pick.v.by:'', al:pick?pick.v.album:'',
        len:pick?pick.v.len:0, ref:ref?ref.sec:0, emb:emb.ok, embSt:emb.st,
        why:pick?(pick.why||''):'sin candidatos', note,
        cand:{atv:tracks.slice(0,2).map(r=>`${Math.round(r.sc)} ${r.v.by} | ${r.v.title} (${r.v.len}s)`),
              omv:vi.filter(v=>v.type==='OMV').slice(0,3).map(v=>`${v.by} | ${v.title} (${v.len}s, ${v.views})`)}});
      done++; if(done%15===0)console.error(done+'/'+songs.length);
      await sleep(70);
    }
  }));
  fs.writeFileSync(DATOS+'/videos.json',JSON.stringify(out,null,1));
  fs.writeFileSync(DATOS+'/videos-informe.json',JSON.stringify(rep,null,1));
  const bad=rep.filter(r=>!r.id||!r.emb||r.src==='pista dudosa');
  console.error('LISTO.  problemas:',bad.length,'de',rep.length);
  bad.forEach(r=>console.error('  ·',r.key,'→',r.src,'|',r.embSt,'|',r.ti,'|',r.why));
})();
