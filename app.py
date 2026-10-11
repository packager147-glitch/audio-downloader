import os
import requests
from flask import Flask, render_template, request, Response

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("url")
        if not video_url:
            return "Please provide a valid URL.", 400

        try:
            # Route requests through a reliable, dedicated media processing instance
            cobalt_url = "https://cobalt.tools"
            
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
            
            # Request processing from Cobalt instance
            api_response = requests.post(cobalt_url, json=payload, headers=headers, timeout=15)
            
            if api_response.status_code != 200:
                return f"Processing failed: {api_response.json().get('text', 'Unknown server challenge')}", 400
                
            download_url = api_response.json().get("url")
            if not download_url:
                return "Could not extract direct stream URL.", 500
                
            # Direct binary stream retrieval to avoid local storage caching
            media_stream = requests.get(download_url, stream=True, timeout=30)
            
            response = Response(
                media_stream.iter_content(chunk_size=4096),
                content_type="audio/mpeg"
            )
            response.headers["Content-Disposition"] = "attachment; filename=audio.mp3"
            return response

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
