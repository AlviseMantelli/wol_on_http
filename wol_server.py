#!/usr/bin/env python3

import subprocess
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from wakeonlan import send_magic_packet
import sys

# --- Configuration ---
TARGET_MAC = '00:11:22:33:44:55'
TARGET_IP = '192.168.1.100'
PORT = 8000

# --- SVG Icons (used in JS and HTML) ---
# Using simple placeholders as most icons will be embedded directly in the HTML/JS for dynamic control
FAVICON_DEFAULT_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#909090"/></svg>'

class RequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the Wake-on-LAN server."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self._serve_html(self.render_main_page())
        elif self.path == '/wol':
            self._send_wol()
        elif self.path == '/ping':
            self._check_ping()
        elif self.path == '/favicon.svg':
            self._serve_favicon()
        else:
            self._send_response(404, 'text/plain', 'Not Found')

    def _send_response(self, code, content_type, body):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def _serve_html(self, html_content):
        self._send_response(200, 'text/html; charset=utf-8', html_content)

    def _send_wol(self):
        try:
            send_magic_packet(TARGET_MAC)
            response = json.dumps({"status": "ok", "message": "Magic Packet sent successfully."})
            self._send_response(200, 'application/json', response)
        except Exception as e:
            response = json.dumps({"status": "error", "message": str(e)})
            self._send_response(500, 'application/json', response)

    def _check_ping(self):
        try:
            param = '-n' if sys.platform == 'win32' else '-c'
            command = ['ping', param, '1', '-W', '1', TARGET_IP]
            is_alive = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        except Exception:
            is_alive = False
        response = json.dumps({'alive': is_alive})
        self._send_response(200, 'application/json', response)

    def _serve_favicon(self):
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.end_headers()
        self.wfile.write(FAVICON_DEFAULT_SVG)

    def render_main_page(self) -> str:
        # NOTE: All literal curly braces for CSS and JS have been doubled (e.g., {{, }})
        # to work correctly inside the Python f-string.
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WOL Controller</title>
    <link id="favicon" rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color-light: #f4f7f9;
            --card-bg-light: rgba(255, 255, 255, 0.7);
            --text-color-light: #2c3e50;
            --text-light-light: #7f8c8d;
            --border-color-light: rgba(0, 0, 0, 0.05);
            --shadow-color-light: rgba(0, 0, 0, 0.1);

            --bg-color-dark: #1c1c1e;
            --card-bg-dark: rgba(44, 44, 46, 0.7);
            --text-color-dark: #e5e5e7;
            --text-light-dark: #8e8e93;
            --border-color-dark: rgba(255, 255, 255, 0.1);
            --shadow-color-dark: rgba(0, 0, 0, 0.3);

            --accent-color: #3498db;
            --accent-hover: #2980b9;
            --online-color: #2ecc71;
            --offline-color: #e74c3c;
            --font-family: 'Poppins', sans-serif;
        }}

        html[data-theme='light'] {{
            --bg-color: var(--bg-color-light);
            --card-bg: var(--card-bg-light);
            --text-color: var(--text-color-light);
            --text-light: var(--text-light-light);
            --border-color: var(--border-color-light);
            --shadow-color: var(--shadow-color-light);
        }}
        html[data-theme='dark'] {{
            --bg-color: var(--bg-color-dark);
            --card-bg: var(--card-bg-dark);
            --text-color: var(--text-color-dark);
            --text-light: var(--text-light-dark);
            --border-color: var(--border-color-dark);
            --shadow-color: var(--shadow-color-dark);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        @keyframes gradient-animation {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translate3d(0, 20px, 0); }}
            to {{ opacity: 1; transform: translate3d(0, 0, 0); }}
        }}

        @keyframes pulse {{
            0% {{ background-color: rgba(128, 128, 128, 0.1); }}
            50% {{ background-color: rgba(128, 128, 128, 0.2); }}
            100% {{ background-color: rgba(128, 128, 128, 0.1); }}
        }}
        
        body {{
            font-family: var(--font-family);
            color: var(--text-color);
            background: linear-gradient(-45deg, var(--bg-color), #eaeaea, var(--bg-color), #f1f1f1);
            background-size: 400% 400%;
            animation: gradient-animation 25s ease infinite;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
            transition: background-color 0.4s ease;
        }}
        html[data-theme='dark'] body {{
             background: linear-gradient(-45deg, var(--bg-color), #2c2c2e, var(--bg-color), #101012);
             background-size: 400% 400%;
             animation: gradient-animation 25s ease infinite;
        }}

        .card {{
            width: 100%;
            max-width: 400px;
            background-color: var(--card-bg);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 20px;
            border: 1px solid var(--border-color);
            border-top-width: 4px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px 0 var(--shadow-color);
            transition: all 0.4s ease;
            animation: fadeInUp 0.8s ease-out forwards;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 var(--shadow-color);
        }}
        .card.online-border {{ border-top-color: var(--online-color); }}
        .card.offline-border {{ border-top-color: var(--offline-color); }}
        
        .skeleton {{
            animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            background-color: rgba(128,128,128,0.1);
            color: transparent !important;
            border-radius: 8px;
        }}
        .skeleton.skeleton-text {{ height: 1.2em; width: 80%; margin: 0.2em auto; }}
        .skeleton.skeleton-title {{ height: 1.5em; width: 60%; margin: 0.2em auto 1rem; }}
        .skeleton.skeleton-info {{ height: 3em; margin-bottom: 1.5rem; }}
        .skeleton.skeleton-status {{ height: 3.2rem; border-radius: 50px; margin-bottom: 1.5rem; }}
        .skeleton.skeleton-button {{ height: 3.5rem; border-radius: 12px; }}

        h1 {{ font-weight: 600; font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .device-info {{ padding: 0.75rem 1rem; margin-bottom: 1.5rem; word-break: break-all; }}
        .device-info strong {{ color: var(--text-color); }}
        .device-info span {{ color: var(--text-light); font-family: 'Menlo', 'Consolas', monospace; }}

        .status {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 0.75rem; border-radius: 50px; margin-top: 1rem; margin-bottom: 1.5rem; font-weight: 600; font-size: 1.1rem; transition: all 0.3s ease; }}
        .status.online {{ background-color: rgba(46, 204, 113, 0.15); color: var(--online-color); }}
        .status.offline {{ background-color: rgba(231, 76, 60, 0.15); color: var(--offline-color); }}
        .status svg {{ width: 24px; height: 24px; }}
        
        #wol-button {{ width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 1rem; font-size: 1rem; font-weight: 600; font-family: var(--font-family); color: #fff; background-color: var(--accent-color); border: none; border-radius: 12px; cursor: pointer; transition: all 0.3s ease; }}
        #wol-button:hover:not(:disabled) {{ background-color: var(--accent-hover); }}
        #wol-button:disabled {{ cursor: not-allowed; background-color: var(--text-light); opacity: 0.7; }}

        #toast {{ visibility: hidden; min-width: 250px; background-color: #333; color: #fff; text-align: center; border-radius: 12px; padding: 16px; position: fixed; z-index: 1; left: 50%; transform: translateX(-50%); bottom: 30px; font-size: 1rem; }}
        #toast.show {{ visibility: visible; animation: toast-fadein 0.5s, toast-fadeout 0.5s 2.5s; }}
        @keyframes toast-fadein {{ from {{ bottom: 0; opacity: 0; }} to {{ bottom: 30px; opacity: 1; }} }}
        @keyframes toast-fadeout {{ from {{ bottom: 30px; opacity: 1; }} to {{ bottom: 0; opacity: 0; }} }}

        #theme-switcher {{ position: fixed; top: 20px; right: 20px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; justify-content: center; align-items: center; }}
        #theme-switcher svg {{ width: 20px; height: 20px; color: var(--text-color); }}
        .icon-sun, .icon-moon {{ display: none; }}
        html[data-theme='light'] .icon-moon {{ display: block; }}
        html[data-theme='dark'] .icon-sun {{ display: block; }}
    </style>
</head>
<body>
    <div class="card" id="main-card">
        <h1 id="card-title" class="skeleton skeleton-title"></h1>
        <div id="device-info" class="skeleton skeleton-info"></div>
        <div id="status-indicator" class="skeleton skeleton-status"></div>
        <div id="wol-button-container" class="skeleton skeleton-button">
            <button id="wol-button" style="display: none;"></button>
        </div>
    </div>
    
    <div id="toast"></div>

    <button id="theme-switcher" title="Toggle Theme">
        <svg class="icon-sun" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707.707M6.343 6.343l-.707-.707m12.728 0l-.707-.707M6.343 17.657l-.707.707M12 12a5 5 0 100-10 5 5 0 000 10z"></path></svg>
        <svg class="icon-moon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>
    </button>
    
    <script>
        // --- DOM Elements ---
        const mainCard = document.getElementById('main-card');
        const cardTitle = document.getElementById('card-title');
        const deviceInfo = document.getElementById('device-info');
        const statusIndicator = document.getElementById('status-indicator');
        const wolButtonContainer = document.getElementById('wol-button-container');
        const wolButton = document.getElementById('wol-button');
        const themeSwitcher = document.getElementById('theme-switcher');
        const favicon = document.getElementById('favicon');

        // --- State ---
        let isInitialLoad = true;

        // --- Icons ---
        const ICONS = {{
            online: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
            offline: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
            wakeUp: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c-5.52 0-10 4.48-10 10s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Z"/><path d="M12 12v5"/><path d="M12 7v1"/></svg>',
        }};
        const FAVICONS = {{
            online: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' xml:space='preserve' id='svg10' x='0' y='0' version='1.1' viewBox='0 0 64 64'%3E%3Cstyle id='style1' type='text/css'%3E.st1%7Bopacity:.2%7D.st2%7Bfill:%23231f20%7D.st3%7Bfill:%23fff%7D%3C/style%3E%3Cg id='Layer_1'%3E%3Cg id='g1'%3E%3Ccircle id='circle1' cx='32' cy='32' r='32' fill='%2337c837'/%3E%3C/g%3E%3Cg id='g2' class='st1'%3E%3Cpath id='path1' d='M44 52a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st2'/%3E%3C/g%3E%3Cg id='g3'%3E%3Cpath id='path2' d='M44 50a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st3'/%3E%3C/g%3E%3Cg id='g4'%3E%3Cpath id='path3' fill='%23e0e0d1' d='M37 42s-1 6 3 6H24c4 0 3-6 3-6h10z'/%3E%3C/g%3E%3Cg id='g6' class='st1'%3E%3Cg id='g5'%3E%3Cpath id='path4' d='M52 40a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4h32a4 4 0 0 1 4 4v22z' class='st2'/%3E%3C/g%3E%3C/g%3E%3Cg id='g9'%3E%3Cg id='g7'%3E%3Cpath id='path6' fill='%234f5d73' d='M16 40.5a2.5 2.5 0 0 1-2.5-2.5V16c0-1.4 1.1-2.5 2.5-2.5h32c1.4 0 2.5 1.1 2.5 2.5v22c0 1.4-1.1 2.5-2.5 2.5H16z'/%3E%3C/g%3E%3Cg id='g8'%3E%3Cpath id='path7' d='M48 15c.6 0 1 .4 1 1v22c0 .6-.4 1-1 1H16c-.6 0-1-.4-1-1V16c0-.6.4-1 1-1h32m0-3H16a4 4 0 0 0-4 4v22a4 4 0 0 0 4 4h32a4 4 0 0 0 4-4V16a4 4 0 0 0-4-4z' class='st3'/%3E%3C/g%3E%3C/g%3E%3Cg id='g10' class='st1'%3E%3Cpath id='polygon9' d='M50 39.9v-26H26.2l15 26z' class='st3'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E",
            offline: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' xml:space='preserve' id='svg10' x='0' y='0' version='1.1' viewBox='0 0 64 64'%3E%3Cstyle id='style1' type='text/css'%3E.st1%7Bopacity:.2%7D.st2%7Bfill:%23231f20%7D.st3%7Bfill:%23fff%7D%3C/style%3E%3Cg id='Layer_1'%3E%3Cg id='g1'%3E%3Ccircle id='circle1' cx='32' cy='32' r='32' fill='%23c83737'/%3E%3C/g%3E%3Cg id='g2' class='st1'%3E%3Cpath id='path1' d='M44 52a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st2'/%3E%3C/g%3E%3Cg id='g3'%3E%3Cpath id='path2' d='M44 50a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st3'/%3E%3C/g%3E%3Cg id='g4'%3E%3Cpath id='path3' fill='%23e0e0d1' d='M37 42s-1 6 3 6H24c4 0 3-6 3-6h10z'/%3E%3C/g%3E%3Cg id='g6' class='st1'%3E%3Cg id='g5'%3E%3Cpath id='path4' d='M52 40a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4h32a4 4 0 0 1 4 4v22z' class='st2'/%3E%3C/g%3E%3C/g%3E%3Cg id='g9'%3E%3Cg id='g7'%3E%3Cpath id='path6' fill='%234f5d73' d='M16 40.5a2.5 2.5 0 0 1-2.5-2.5V16c0-1.4 1.1-2.5 2.5-2.5h32c1.4 0 2.5 1.1 2.5 2.5v22c0 1.4-1.1 2.5-2.5 2.5H16z'/%3E%3C/g%3E%3Cg id='g8'%3E%3Cpath id='path7' d='M48 15c.6 0 1 .4 1 1v22c0 .6-.4 1-1 1H16c-.6 0-1-.4-1-1V16c0-.6.4-1 1-1h32m0-3H16a4 4 0 0 0-4 4v22a4 4 0 0 0 4 4h32a4 4 0 0 0 4-4V16a4 4 0 0 0-4-4z' class='st3'/%3E%3C/g%3E%3C/g%3E%3Cg id='g10' class='st1'%3E%3Cpath id='polygon9' d='M50 39.9v-26H26.2l15 26z' class='st3'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E",
            checking: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' xml:space='preserve' id='svg10' x='0' y='0' version='1.1' viewBox='0 0 64 64'%3E%3Cstyle id='style1' type='text/css'%3E.st1%7Bopacity:.2%7D.st2%7Bfill:%23231f20%7D.st3%7Bfill:%23fff%7D%3C/style%3E%3Cg id='Layer_1'%3E%3Cg id='g1'%3E%3Ccircle id='circle1' cx='32' cy='32' r='32' fill='%23ffd42a'/%3E%3C/g%3E%3Cg id='g2' class='st1'%3E%3Cpath id='path1' d='M44 52a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st2'/%3E%3C/g%3E%3Cg id='g3'%3E%3Cpath id='path2' d='M44 50a2 2 0 0 1-2 2H22a2 2 0 0 1-2-2c0-1.1.9-2 2-2h20a2 2 0 0 1 2 2z' class='st3'/%3E%3C/g%3E%3Cg id='g4'%3E%3Cpath id='path3' fill='%23e0e0d1' d='M37 42s-1 6 3 6H24c4 0 3-6 3-6h10z'/%3E%3C/g%3E%3Cg id='g6' class='st1'%3E%3Cg id='g5'%3E%3Cpath id='path4' d='M52 40a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4h32a4 4 0 0 1 4 4v22z' class='st2'/%3E%3C/g%3E%3C/g%3E%3Cg id='g9'%3E%3Cg id='g7'%3E%3Cpath id='path6' fill='%234f5d73' d='M16 40.5a2.5 2.5 0 0 1-2.5-2.5V16c0-1.4 1.1-2.5 2.5-2.5h32c1.4 0 2.5 1.1 2.5 2.5v22c0 1.4-1.1 2.5-2.5 2.5H16z'/%3E%3C/g%3E%3Cg id='g8'%3E%3Cpath id='path7' d='M48 15c.6 0 1 .4 1 1v22c0 .6-.4 1-1 1H16c-.6 0-1-.4-1-1V16c0-.6.4-1 1-1h32m0-3H16a4 4 0 0 0-4 4v22a4 4 0 0 0 4 4h32a4 4 0 0 0 4-4V16a4 4 0 0 0-4-4z' class='st3'/%3E%3C/g%3E%3C/g%3E%3Cg id='g10' class='st1'%3E%3Cpath id='polygon9' d='M50 39.9v-26H26.2l15 26z' class='st3'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E",
        }};
        
        // --- Functions ---
        
        function removeSkeletons() {{
            cardTitle.classList.remove('skeleton', 'skeleton-title');
            deviceInfo.classList.remove('skeleton', 'skeleton-info');
            statusIndicator.classList.remove('skeleton', 'skeleton-status');
            wolButtonContainer.classList.remove('skeleton', 'skeleton-button');
            wolButton.style.display = 'flex';
        }}

        function setFavicon(status) {{
            favicon.href = FAVICONS[status] || FAVICONS.checking;
        }}
        
        async function checkStatus() {{
            try {{
                const response = await fetch('/ping');
                const data = await response.json();
                
                if (isInitialLoad) {{
                    removeSkeletons();
                    isInitialLoad = false;
                }}

                if (data.alive) {{
                    statusIndicator.className = 'status online';
                    statusIndicator.innerHTML = `${{ICONS.online}} <span>Online</span>`;
                    mainCard.classList.add('online-border');
                    mainCard.classList.remove('offline-border');
                    setFavicon('online');
                }} else {{
                    statusIndicator.className = 'status offline';
                    statusIndicator.innerHTML = `${{ICONS.offline}} <span>Offline</span>`;
                    mainCard.classList.add('offline-border');
                    mainCard.classList.remove('online-border');
                    setFavicon('offline');
                }}
            }} catch (error) {{
                console.error("Ping failed:", error);
                statusIndicator.className = 'status offline';
                statusIndicator.innerHTML = `${{ICONS.offline}} <span>Status Unknown</span>`;
                setFavicon('offline');
            }}
        }}

        function showToast(message) {{
            const toast = document.getElementById("toast");
            toast.textContent = message;
            toast.className = "show";
            setTimeout(() => {{ toast.className = toast.className.replace("show", ""); }}, 3000);
        }}

        async function sendWol() {{
            wolButton.disabled = true;
            wolButton.innerHTML = `<span>Sending...</span>`;
            
            try {{
                await fetch('/wol');
                showToast("Magic Packet sent successfully ✔️");
            }} catch (error) {{
                console.error("WOL failed:", error);
                showToast("Failed to send packet ❌");
            }}
            
            setTimeout(() => {{
                wolButton.disabled = false;
                wolButton.innerHTML = `${{ICONS.wakeUp}} <span>Wake Up Device</span>`;
            }}, 2000);
        }}

        // --- Theme Management ---
        function applyTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        }}

        themeSwitcher.addEventListener('click', () => {{
            const currentTheme = localStorage.getItem('theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
        }});

        // --- Initial Load ---
        document.addEventListener('DOMContentLoaded', () => {{
            // Set initial theme
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

            // Populate static content
            cardTitle.textContent = "Device Controller";
            deviceInfo.innerHTML = `<strong>IP:</strong> <span>{TARGET_IP}</span><br><strong>MAC:</strong> <span>{TARGET_MAC}</span>`;
            wolButton.innerHTML = `${{ICONS.wakeUp}} <span>Wake Up Device</span>`;
            
            // Add listeners
            wolButton.addEventListener('click', sendWol);
            
            // Start status polling
            setFavicon('checking');
            checkStatus();
            setInterval(checkStatus, 1000);
        }});

    </script>
</body>
</html>
'''


def run():
    """Starts the HTTP server."""
    try:
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, RequestHandler)
        print(f"✅ Server running on http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()
    except OSError as e:
        print(f"❌ Error: Could not start server on port {PORT}. It might be in use.")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == '__main__':
    run()