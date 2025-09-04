import http.server
import socketserver
import requests
import json
import re

PORT = 8000
DISCORD_API_BASE_URL = 'https://discord.com/api/v10'

class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # Handle POST requests for creating DM channels and sending messages
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            # Extract token from the Authorization header
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bot '):
                self.send_error(401, 'Unauthorized')
                return

            token = auth_header.split(' ')[1]

            # Determine the API endpoint based on the path
            if self.path == '/api/users/@me/channels':
                url = f"{DISCORD_API_BASE_URL}/users/@me/channels"
                payload = {'recipient_id': data['recipient_id']}
            elif re.match(r'/api/channels/\d+/messages', self.path):
                url = f"{DISCORD_API_BASE_URL}{self.path}"
                payload = {'content': data['content']}
            else:
                self.send_error(404, 'Not Found')
                return

            headers = {
                'Authorization': f'Bot {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Discord-Mass-DM-Tool/1.0'
            }
            
            # Forward the request to the Discord API
            discord_response = requests.post(url, headers=headers, json=payload)
            
            # Respond to the client with the Discord API's response
            self.send_response(discord_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(discord_response.content)

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.send_error(400, f'Bad Request: {e}')
        except Exception as e:
            self.send_error(500, f'Internal Server Error: {e}')

    def do_GET(self):
        # Handle GET requests for fetching guild members
        try:
            # Extract token from the Authorization header
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bot '):
                self.send_error(401, 'Unauthorized')
                return
            
            token = auth_header.split(' ')[1]

            # Check if the request is for guild members
            match = re.match(r'/api/guilds/(\d+)/members\?limit=1000', self.path)
            if match:
                guild_id = match.group(1)
                url = f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/members?limit=1000"
                headers = {
                    'Authorization': f'Bot {token}',
                    'User-Agent': 'Discord-Mass-DM-Tool/1.0'
                }

                # Forward the request to the Discord API
                discord_response = requests.get(url, headers=headers)
                
                # Respond to the client with the Discord API's response
                self.send_response(discord_response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(discord_response.content)
            else:
                # Serve the HTML file for other GET requests
                return http.server.SimpleHTTPRequestHandler.do_GET(self)

        except Exception as e:
            self.send_error(500, f'Internal Server Error: {e}')

with socketserver.TCPServer(('', PORT), CORSProxyHandler) as httpd:
    print(f"Serving Discord DM Tool with CORS proxy at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server.")
    httpd.serve_forever()
