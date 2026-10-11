import io
import os
import urllib.request
from flask import Flask, render_template, request, Response
from pytubefix import YouTube
from pytubefix.cli import on_progress

app = Flask(__name__)

def fetch_working_proxy():
    """Scrapes a fresh, active public proxy to bypass the Render 429 IP ban."""
    try:
        # Fetch list of active public proxies (HTTP protocol, 5-second timeout)
        api_url = "https://proxyscrape.com"
        response = urllib.request.urlopen(api_url, timeout=5)
        raw_proxies = response.read().decode('utf-8').strip().split('\n')
        
        valid_proxies = [p.strip() for p in raw_proxies if p.strip() and not p.startswith('##')]
        if valid_proxies:
            proxy_ip = valid_proxies[0]
            # Structure the proxy dictionary for pytubefix
            return {
                "http": f"http://{proxy_ip}",
                "https": f"http://{proxy_ip}"
            }
    except Exception:
        pass
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("url")
        if not video_url:
            return "Please provide a valid URL.", 400

        try:
            # Dynamically fetch a fresh proxy connection route
            proxy_config = fetch_working_proxy()
            
            # Initialize connection passing the proxy along with the WEB client engine
            if proxy_config:
                yt = YouTube(video_url, client='WEB', proxies=proxy_config, on_progress_callback=on_progress)
            else:
                yt = YouTube(video_url, client='WEB', on_progress_callback=on_progress)
            
            # Extract pure high-quality audio stream tracks
            audio_stream = yt.streams.get_audio_only()
            if not audio_stream:
                return "No playable audio stream detected on this video.", 404
                
            # Clean up the file name characters for browser attachment
            clean_title = "".join([c for c in yt.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{clean_title or 'audio'}.mp3"

            # Stream the media data strictly into memory buffers
            buffer = io.BytesIO()
            audio_stream.stream_to_buffer(buffer)
            buffer.seek(0)

            # Generate chunks to pass to standard user download
            def generate():
                while True:
                    chunk = buffer.read(4096)
                    if not chunk:
                        break
                    yield chunk

            response = Response(generate(), content_type="audio/mpeg")
            response.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
            return response

        except Exception as e:
            return f"The server is unable to process this video link. Details: <br>{str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
