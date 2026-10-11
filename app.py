import os
import requests
from flask import Flask, render_template, request, Response

app = Flask(__name__)

# List of distributed, active backup instances to cycle through if one blocks us
COBALT_INSTANCES = [
    "https://cobalt.tools",
    "https://v0.pw",
    "https://cobalt.lol"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("url")
        if not video_url:
            return "Please provide a valid URL.", 400

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": video_url,
            "downloadMode": "audio",
            "audioFormat": "mp3",
            "audioBitrate": "320"
        }

        download_url = None
        error_logs = []

        # Loop through available instances until one successfully parses valid JSON
        for base_url in COBALT_INSTANCES:
            try:
                api_response = requests.post(base_url, json=payload, headers=headers, timeout=10)
                
                # Check if the response is actually valid JSON text before decoding it
                if "application/json" in api_response.headers.get("Content-Type", ""):
                    json_data = api_response.json()
                    
                    if api_response.status_code == 200 and "url" in json_data:
                        download_url = json_data.get("url")
                        break
                    else:
                        error_logs.append(f"{base_url}: {json_data.get('text', 'Instance Error')}")
                else:
                    error_logs.append(f"{base_url}: Returned invalid text/HTML instead of JSON")
                    
            except Exception as e:
                error_logs.append(f"{base_url} failed: {str(e)}")

        # Catch-all validation if every single server in the pool drops the request
        if not download_url:
            return f"All processing servers are currently busy. Details: <br>{'<br>'.join(error_logs)}", 503

        try:
            # Stream the confirmed media file back to the user's browser immediately
            media_stream = requests.get(download_url, stream=True, timeout=30)
            
            response = Response(
                media_stream.iter_content(chunk_size=4096),
                content_type="audio/mpeg"
            )
            response.headers["Content-Disposition"] = "attachment; filename=audio.mp3"
            return response

        except Exception as e:
            return f"Failed to pipe the file down: {str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
