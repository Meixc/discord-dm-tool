from flask import Flask, request, jsonify, make_response
import requests
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DISCORD_API_BASE_URL = 'https://discord.com/api/v10'

# A proxy that forwards requests to the Discord API
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_discord_api(path):
    print(f"Proxying request to Discord API: {request.method} {path}")
    try:
        # Reconstruct the headers from the incoming request
        headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'connection']}
        
        # Add a custom User-Agent to comply with Discord's API policy
        headers['User-Agent'] = 'Discord-Mass-DM-Tool/1.0'

        # Get the request body if present
        data = None
        if request.data:
            data = request.data
        
        # Forward the request to the Discord API
        response = requests.request(
            method=request.method,
            url=f"{DISCORD_API_BASE_URL}/{path}",
            headers=headers,
            data=data
        )

        # Prepare the response to send back to the client
        proxy_response = make_response(response.content, response.status_code)

        # Copy all headers from the original response
        for key, value in response.headers.items():
            proxy_response.headers[key] = value

        # Set CORS headers on the response
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        proxy_response.headers['Access-Control-Allow-Headers'] = '*'
        
        print(f"Forwarded response with status code: {response.status_code}")
        return proxy_response

    except requests.exceptions.RequestException as e:
        print(f"Error during proxy request: {e}")
        return jsonify({
            "error": "Failed to proxy request",
            "details": str(e)
        }), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    print("Serving Discord DM Tool with CORS proxy at http://localhost:8000")
    print("Make sure you have `pip install Flask requests Flask-Cors` installed.")
    print("Press Ctrl+C to stop the server.")
    app.run(port=8000)
