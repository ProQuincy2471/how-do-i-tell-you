# How do I tell you? ...

Una playlist de 190 canciones convertida en una página interactiva. De Jordan, para Ana.

## Qué es esto

Un **único archivo HTML** (`index.html`, ~330 KB): sin build, sin dependencias, sin
framework. Se edita a mano y se abre. Todo el estado del usuario (escuchadas,
favoritas, notas, ediciones) vive en `localStorage` bajo la clave `hditu_v2`.

Las 190 canciones están en la constante `ACTS` dentro del propio HTML, repartidas
en 6 grupos. Los grupos se llaman **Nebulosa I–VI**; internamente los datos dicen
`"Acto I"` y la función `relabel()` sustituye el prefijo según `ST.prefs.label`
(las opciones están en `LABELS`). No hay que tocar los datos para renombrarlos.

## Dónde vive

Repo: **github.com/ProQuincy2471/how-do-i-tell-you** (público, cuenta `ProQuincy2471`
vía `gh`). El remoto se llama `origin`, rama `main`. Publicado también con
**GitHub Pages** en https://proquincy2471.github.io/how-do-i-tell-you/ — se
redespliega solo con cada push a `main`, así que esa URL siempre es la versión
más reciente, instalable como PWA desde el celular (Agregar a pantalla de inicio).

Después de cada tanda de cambios que el usuario pida guardar: `git commit` y
**`git push origin main`** — el usuario quiere que GitHub siempre tenga lo último
corriendo, no solo el commit local.

La app es también una **PWA**: `manifest.json` + `sw.js` (service worker
red-primero, caché solo como respaldo sin conexión — nunca al revés, para no
repetir el problema de contenido viejo que el `no-store` del servidor local ya
resuelve). Los íconos están en `icons/`, generados con Pillow
(fondo oscuro + estrella dorada, mismo lenguaje visual que el resto de la app).

## Cómo se abre

Doble clic en **`abrir.command`**. Levanta un servidor local en
http://localhost:8123 y abre el navegador.

**No sirve abrirlo con `file://`**: el navegador niega los permisos de audio y de
almacenamiento fuera de un origen seguro.

Dos detalles del servidor que costaron sangre y conviene no deshacer:

- Usa **`ThreadingHTTPServer`**, no `TCPServer`. El navegador mantiene varias
  conexiones abiertas a la vez; con un servidor de un solo hilo se queda
  bloqueado en una de ellas y la página se cuelga sin dar ningún error.
- Manda **`Cache-Control: no-store`** y descarta las peticiones condicionales.
  Sin eso el navegador reutiliza la copia vieja y los cambios no se ven aunque el
  archivo en disco esté actualizado. Además cada arranque abre una URL con una
  marca de tiempo distinta.

Abajo a la izquierda de la página hay un **sello de versión** (`const BUILD`).
Sirve para saber de un vistazo si el navegador está mostrando la última versión.
Conviene actualizarlo en cada cambio.

## Estructura

```
index.html          la página entera
abrir.command       servidor local (doble clic)
herramientas/       scripts que generaron los datos incrustados en el HTML
  resolver-videos.js      IDs de YouTube (node herramientas/resolver-videos.js)
  portadas-itunes.py      portadas reales desde la API de iTunes
  paletas-de-portada.py   4 colores por portada (cuantización + puntuación HLS)
  generar-cielo.py        catálogo de estrellas reales → sky.js
  datos/                  salidas y catálogos de origen
archivo/            versiones antiguas, por si acaso
```

## Cómo se eligen los vídeos de YouTube

`herramientas/resolver-videos.js`. La regla importante: **no usar la búsqueda web
de YouTube**, porque devuelve reuploads del propio canal del artista (dance
practices, monitoring clips, «M/V COPY») y canales de fans. Se usa la API interna
de **YouTube Music** (`music.youtube.com/youtubei/v1/search`, cliente
`WEB_REMIX`), que etiqueta cada resultado:

- `OMV` = vídeo musical oficial
- `ATV` = audio oficial (lo mismo que sirve el canal «<Artista> - Topic»)
- `UGC` = subida de usuario → **nunca**

Se elige el OMV más visto si dura casi lo mismo que la pista; si no (cortos,
directos, montajes), el ATV. La duración de iTunes arbitra y `oembed` confirma
que el vídeo sigue vivo. Estado actual: 115 vídeos oficiales, 74 audios oficiales.

## La vista Constelación

Las 190 canciones son estrellas repartidas en 18 figuras dibujadas sobre el cielo
real (1627 estrellas del catálogo Yale, las 88 constelaciones con sus líneas, la
Vía Láctea y objetos Messier).

El reparto de las figuras usa **muestreo por disco de Poisson** (Bridson). No usar
relajación de Lloyd: reparte muy bien pero converge a una teselación centroidal,
o sea a una retícula visible — ya pasó, y se notaba muchísimo.

El bucle de dibujo se pausa a propósito cuando `document.hidden` es cierto. Si el
lienzo aparece negro, casi siempre es eso y no un fallo.

## El modo Letras

La pestaña **Letras** (o la tecla `l`) es la cola de trabajo para ir pegando letras:
lista las canciones que aún no tienen, con enlaces de búsqueda por canción
(Genius, Musixmatch, letras.com, Google), y abre una pizarra a doble columna
—original y traducción— con «Guardar y siguiente» (`⌘/ctrl + ↵`). Guarda en
`ST.edits.songs[key].og/.es`, igual que el editor ✎; la constante `LYRICS` del
HTML solo sirve para dejar letras por defecto en el código.

## Íconos, recuerdos y navegación (renovación de oct-2026)

- **Íconos: Lucide** (lucide.dev, ISC), incrustados como SVG en la constante `KP` — sin red. No dibujar
  íconos a mano. Para cada recuerdo el ícono se elige por el **sentido completo** del recuerdo, no por una
  palabra suelta del texto (ver comentarios en `MEM_META`). Para añadir uno: bajar el SVG de
  `cdn.jsdelivr.net/npm/lucide-static@latest/icons/<nombre>.svg` y meter su interior en `KP`.
- **Carta → recuerdos**: esferas de cristal con tamaños distintos y posiciones al azar con semilla
  (muestreo con distancia mínima, `layoutMemories`); solo un balanceo lento en `memLoop`. No volver a
  meter relajación por pares ni imán al cursor: era lo que se sentía como sacudidas.
- **Voces** es una *partitura*: filas = artistas, columnas = Nebulosas, puntos = canciones.
- **Constelación**: zoom exponencial y hover con histéresis (el cursor no salta de estrella en estrella);
  minimapa (`#cmini`) y recorrido guiado (`TOUR`).
- **Navegación**: rutas con hash (`#voces`…), atrás/adelante, memoria de pestaña y scroll, teclas 1–6,
  barra de pestañas inferior en móvil (`#tabbar`, ≤760px).

## Versión 2.0: mundos (oct-2026)

Cada pestaña es un *mundo* con su propio material; `go()` pone `body[data-v=…]` y el color de acento
(`--vacc`, animado con `@property`). Claros: **Voces** y **Carta** (papel crema; los recuerdos viven en una
banda oscura `.mem-band` dentro de la carta). Lo que flota encima (modales, dock, fichas, barra lateral) siempre
usa la paleta oscura: se reinicia con `body>*:not(#shell)` — si añades un overlay nuevo, cuélgalo del `body`.
Barra lateral izquierda en compu (`header` fijo, se expande al pasar el cursor), barra inferior en móvil.
Tipografías: Fraunces (títulos), Bricolage Grotesque (UI), DM Mono (Letras), Caveat (a mano).

## Que sea la canción correcta

Los IDs de YouTube viven en `const YTIDS` (index.html) y las portadas/álbumes en `const COV`. Antes de dar por
buena una lista de IDs corre **`python3 herramientas/auditar-videos.py`**: pregunta a YouTube el título y canal de
cada vídeo y avisa de otro artista, otra versión (ensayo, fancam, directo) o subidas no oficiales. El resolvedor
exige que el artista coincida (antes un título exacto bastaba y salían canciones de otro artista).
Si una portada de iTunes no es del artista/versión, se borra de `COV`: la app cae a la miniatura del propio vídeo.
""
## Trampas conocidas

- `cur` es la canción **enfocada** (cambia al abrir una ficha); `playing` es la
  que **suena**. No confundirlas.
- Al saltar de canción hay que hacer `stopVideo()` antes de `loadVideoById()`: si
  se solapan, se oyen las dos pistas desfasadas y suena desafinado.
- «Only One» y «Walk Thru Fire» aparecen **dos veces** en la playlist. Cada
  aparición tiene su propia clave (`key`), pero comparten `base` para buscar
  portada y color.
- Varios **títulos se repiten entre artistas distintos** (p. ej. dos canciones
  llamadas «Stuck In The Middle», una de Ran-D/Vertile y otra de BABYMONSTER —
  esta última es el epígrafe del Acto IV, que se llama igual). Buscar una
  canción solo por título (`SONGS.find(x=>x.t===q)`) puede traer la
  equivocada. Para resolver la cita/epígrafe de un acto, usar `quoteSong(a,q)`
  — prioriza la que está dentro del propio acto antes que la primera
  coincidencia global.
- Los textos de las canciones son citas del usuario. **No inventar letras**: la
  página tiene un editor para pegarlas (y soporta formato LRC sincronizado).
