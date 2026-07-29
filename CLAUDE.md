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

## Trampas conocidas

- `cur` es la canción **enfocada** (cambia al abrir una ficha); `playing` es la
  que **suena**. No confundirlas.
- Al saltar de canción hay que hacer `stopVideo()` antes de `loadVideoById()`: si
  se solapan, se oyen las dos pistas desfasadas y suena desafinado.
- «Only One» y «Walk Thru Fire» aparecen **dos veces** en la playlist. Cada
  aparición tiene su propia clave (`key`), pero comparten `base` para buscar
  portada y color.
- Los textos de las canciones son citas del usuario. **No inventar letras**: la
  página tiene un editor para pegarlas (y soporta formato LRC sincronizado).
