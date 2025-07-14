#!/usr/bin/env python3

import subprocess
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from wakeonlan import send_magic_packet

# Da modificare con i valori corretti
TARGET_MAC = '00:11:22:33:44:55'
TARGET_IP = '0.0.0.0'
PORT = 8000

FAVICON_SVG = b'''<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: Adobe Illustrator 19.1.0, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 viewBox="0 0 64 64" style="enable-background:new 0 0 64 64;" xml:space="preserve">
<style type="text/css">
	.st0{fill:#76C2AF;}
	.st1{opacity:0.2;}
	.st2{fill:#231F20;}
	.st3{fill:#FFFFFF;}
	.st4{fill:#E0E0D1;}
	.st5{fill:#4F5D73;}
</style>
<g id="Layer_1">
	<g>
		<circle class="st0" cx="32" cy="32" r="32"/>
	</g>
	<g class="st1">
		<path class="st2" d="M44,52c0,1.1-0.9,2-2,2H22c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h20C43.1,50,44,50.9,44,52L44,52z"/>
	</g>
	<g>
		<path class="st3" d="M44,50c0,1.1-0.9,2-2,2H22c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h20C43.1,48,44,48.9,44,50L44,50z"/>
	</g>
	<g>
		<path class="st4" d="M37,42c0,0-1,6,3,6c0,0-20,0-16,0s3-6,3-6H37z"/>
	</g>
	<g class="st1">
		<g>
			<path class="st2" d="M52,40c0,2.2-1.8,4-4,4H16c-2.2,0-4-1.8-4-4V18c0-2.2,1.8-4,4-4h32c2.2,0,4,1.8,4,4V40z"/>
		</g>
	</g>
	<g>
		<g>
			<path class="st5" d="M16,40.5c-1.4,0-2.5-1.1-2.5-2.5V16c0-1.4,1.1-2.5,2.5-2.5h32c1.4,0,2.5,1.1,2.5,2.5v22
				c0,1.4-1.1,2.5-2.5,2.5H16z"/>
		</g>
		<g>
			<path class="st3" d="M48,15c0.6,0,1,0.4,1,1v22c0,0.6-0.4,1-1,1H16c-0.6,0-1-0.4-1-1V16c0-0.6,0.4-1,1-1H48 M48,12H16
				c-2.2,0-4,1.8-4,4v22c0,2.2,1.8,4,4,4h32c2.2,0,4-1.8,4-4V16C52,13.8,50.2,12,48,12L48,12z"/>
		</g>
	</g>
	<g class="st1">
		<polygon class="st3" points="50,39.9 50,13.9 26.2,13.9 41.2,39.9 		"/>
	</g>
</g>
<g id="Layer_2">
</g>
</svg>
'''

# SVG icons for status, inline for cleaner look:
SVG_CHECK = '''<svg style="vertical-align:middle" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#188038" viewBox="0 0 24 24"><path d="M20.285 6.707l-11.39 11.39-5.657-5.657 1.414-1.414 4.243 4.243 9.975-9.975z"/></svg>'''
SVG_CROSS = '''<svg style="vertical-align:middle" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#d93025" viewBox="0 0 24 24"><path d="M18.364 5.636l-1.414-1.414L12 9.172 7.05 4.222 5.636 5.636 10.586 10.586 5.636 15.536l1.414 1.414L12 12l4.95 4.95 1.414-1.414-4.95-4.95z"/></svg>'''

class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/wol':
            try:
                send_magic_packet(TARGET_MAC)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Wake-on-LAN Sent</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
  body {{
    margin: 0;
    background: #fff;
    font-family: 'Roboto', sans-serif;
    color: #202124;
    display: flex;
    height: 100vh;
    justify-content: center;
    align-items: center;
  }}
  .card {{
    background: #f8f9fa;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
    max-width: 360px;
    width: 90vw;
    text-align: center;
  }}
  h1 {{
    font-weight: 500;
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: #1a73e8;
  }}
  .mac {{
    font-weight: 500;
    color: #3c4043;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
  }}
  #status {{
    font-weight: 600;
    font-size: 1.3rem;
    padding: 0.75rem 1.5rem;
    border-radius: 30px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    user-select: none;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.15);
    transition: background-color 0.3s ease, color 0.3s ease;
    min-width: 190px;
    justify-content: center;
  }}
  #status.online {{
    background-color: #e6f4ea;
    color: #188038;
  }}
  #status.offline {{
    background-color: #fce8e6;
    color: #d93025;
  }}
</style>
<script>
const SVG_CHECK = `{SVG_CHECK}`;
const SVG_CROSS = `{SVG_CROSS}`;

async function checkPing() {{
  try {{
    const res = await fetch('/ping');
    const data = await res.json();
    const status = document.getElementById('status');
    if(data.alive) {{
      status.innerHTML = SVG_CHECK + ' Device is <strong>ONLINE</strong>';
      status.classList.remove('offline');
      status.classList.add('online');
    }} else {{
      status.innerHTML = SVG_CROSS + ' Device is <strong>OFFLINE</strong>';
      status.classList.remove('online');
      status.classList.add('offline');
    }}
  }} catch(e) {{
    console.error('Ping error:', e);
  }}
}}
setInterval(checkPing, 1000);
checkPing();
</script>
</head>
<body>
  <div class="card">
    <h1>Magic Packet Sent</h1>
    <div class="mac">{TARGET_MAC}</div>
    <div id="status" class="offline">Checking status...</div>
  </div>
</body>
</html>'''
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(f'<h1>Error sending WOL packet</h1><p>{e}</p>'.encode('utf-8'))

        elif self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            alive = False
            try:
                res = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', TARGET_IP],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                alive = (res.returncode == 0)
            except Exception:
                alive = False
            self.wfile.write(json.dumps({'alive': alive}).encode('utf-8'))

        elif self.path == '/favicon.svg':
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.end_headers()
            self.wfile.write(FAVICON_SVG)

        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Not found\n')

def run():
    server = HTTPServer(('', PORT), RequestHandler)
    print(f'Serving on port {PORT}...')
    server.serve_forever()

if __name__ == '__main__':
    run()
