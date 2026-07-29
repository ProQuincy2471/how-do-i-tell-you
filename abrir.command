#!/bin/bash
# ── How do I tell you? ...  ·  servidor local ──
# Doble clic para abrir. Sirve la página en http://localhost:8123
# (Hace falta servirla desde localhost, no con file://: el navegador solo
#  concede permisos de audio y almacenamiento en un origen seguro.)
#
# Sirve con Cache-Control: no-store para que el navegador nunca se quede
# con una versión vieja de la página después de una actualización.

cd "$(dirname "$0")" || exit 1
PORT=8123

# si el puerto ya está ocupado, sube hasta encontrar uno libre
while lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT+1))
done

echo ""
echo "  How do I tell you? ...   →  http://localhost:$PORT"
echo "  Deja esta ventana abierta mientras la usas."
echo "  Para cerrar el servidor: Ctrl-C"
echo ""

# la marca de tiempo hace que cada arranque sea una URL nueva para el
# navegador: así jamás puede reutilizar una copia vieja de la página
sleep 1 && open "http://localhost:$PORT/?b=$(date +%s)" &

exec python3 - "$PORT" <<'PY'
import sys, http.server

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def send_head(self):
        # ignora las peticiones condicionales: siempre devuelve el archivo actual
        for h in ('If-Modified-Since', 'If-None-Match'):
            if h in self.headers:
                del self.headers[h]
        return super().send_head()

    def log_message(self, *a):
        pass

# ThreadingHTTPServer, no TCPServer: el navegador mantiene varias conexiones
# abiertas a la vez y un servidor de un solo hilo se queda bloqueado en una
# de ellas, dejando la página colgada.
http.server.ThreadingHTTPServer.allow_reuse_address = True
http.server.ThreadingHTTPServer.daemon_threads = True
with http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), NoCache) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  servidor cerrado')
PY
