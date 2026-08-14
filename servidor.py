#!/usr/bin/env python3
"""Servidor local de la página — el mismo que levanta abrir.command.

Existe aparte para poder arrancarlo sin doble clic:

    python3 servidor.py [puerto]

abrir.command es lo cómodo en el día a día (doble clic y abre el navegador);
esto es lo mismo sin abrir nada, para arrancarlo desde una terminal o desde
una herramienta que no puede ejecutar un .command.

Dos cosas que conviene no tocar (están explicadas en CLAUDE.md):
  · ThreadingHTTPServer, no TCPServer — el navegador mantiene varias
    conexiones abiertas y un servidor de un hilo se queda colgado en una.
  · Cache-Control: no-store y las peticiones condicionales descartadas — sin
    eso el navegador reutiliza la copia vieja y los cambios no se ven.
"""
import sys, http.server, functools
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8123


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


http.server.ThreadingHTTPServer.allow_reuse_address = True
http.server.ThreadingHTTPServer.daemon_threads = True
handler = functools.partial(NoCache, directory=str(RAIZ))

with http.server.ThreadingHTTPServer(('127.0.0.1', PUERTO), handler) as httpd:
    print(f'  How do I tell you? ...   →  http://localhost:{PUERTO}', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  servidor cerrado')
