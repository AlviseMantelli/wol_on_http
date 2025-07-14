#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from wakeonlan import send_magic_packet

# Questi valori saranno sostituiti dallo script di installazione
TARGET_MAC = '00:00:00:00:00:00'
PORT = 8000

# Semplice favicon SVG (puoi sostituire con la tua)
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

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/wol':
            try:
                send_magic_packet(TARGET_MAC)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                # HTML responsive e semplice con Trebuchet MS
                html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Wake-on-LAN Sent</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
  body {{
    font-family: 'Roboto', 'Trebuchet MS', sans-serif;
    background: #f5f5f5;
    color: #212121;
    margin: 0;
    padding: 0;
    display: flex;
    height: 100vh;
    justify-content: center;
    align-items: center;
  }}
  .card {{
    background: white;
    padding: 2rem 3rem;
    border-radius: 12px;
    box-shadow: 0 6px 10px rgba(0,0,0,0.1), 0 1px 18px rgba(0,0,0,0.06);
    max-width: 400px;
    width: 90%;
    text-align: center;
  }}
  h1 {{
    font-weight: 500;
    font-size: 2.2rem;
    color: #4caf50; /* Material green */
    margin-bottom: 0.3rem;
  }}
  p {{
    font-weight: 400;
    font-size: 1.1rem;
    margin: 0.5rem 0;
    color: #616161;
  }}
  .mac {{
    font-weight: 500;
    font-size: 1.3rem;
    color: #212121;
    margin-top: 1rem;
    letter-spacing: 2px;
  }}
  .button {{
    margin-top: 2rem;
    background-color: #4caf50;
    border: none;
    color: white;
    padding: 0.75rem 2rem;
    font-size: 1rem;
    border-radius: 24px;
    cursor: pointer;
    box-shadow: 0 3px 5px rgba(76,175,80,0.4);
    transition: background-color 0.3s ease, box-shadow 0.3s ease;
    user-select: none;
    text-transform: uppercase;
    font-weight: 500;
  }}
  .button:hover {{
    background-color: #43a047;
    box-shadow: 0 5px 10px rgba(67,160,71,0.6);
  }}
  @media (max-width: 600px) {{
    .card {{
      padding: 1.5rem 2rem;
      max-width: 95%;
    }}
    h1 {{
      font-size: 1.8rem;
    }}
    .button {{
      width: 100%;
      padding: 0.75rem 0;
    }}
  }}
</style>
</head>
<body>
  <div class="card">
    <h1>✔️ Magic Packet Sent!</h1>
    <p>Your Wake-on-LAN packet has been successfully sent to:</p>
    <div class="mac">{TARGET_MAC}</div>
    <button class="button" onclick="location.reload()">Send Again</button>
  </div>
</body>
</html>'''

                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                error_html = f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8" /><title>Error</title></head>
<body>
<h1>❌ Failed to send Magic Packet</h1>
<p>{str(e)}</p>
</body>
</html>'''
                self.wfile.write(error_html.encode('utf-8'))
        elif self.path == '/favicon.svg':
            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            self.wfile.write(FAVICON_SVG)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Invalid endpoint\n')

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Listening on port {PORT}... (GET /wol to trigger WOL)")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
