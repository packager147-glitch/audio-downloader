import io
import os
import sys
import urllib.request
import re
from flask import Flask, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

def get_free_proxy():
    """Scrapes a fresh public proxy to bypass YouTube's data center block."""
    try:
        url = "https://proxyscrape.com"
        response = urllib.request.urlopen(url, timeout=5)
        proxies = response.read().decode('utf-8').strip().split('\n')
        valid_proxies = [p.strip() for p in proxies if p.strip() and not p.startswith('##')]
        if valid_proxies:
            # Return the first available working proxy option
            return f"http://{valid_proxies[0]}"
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
            # Dynamically fetch a fresh proxy connection string
            proxy_server = get_free_proxy()

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '-',  
                'logtostderr': True,
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['mweb'],
                        'skip': ['webpage', 'configs'],
                    }
                }
            }

            # Inject the routing proxy into options if successfully retrieved
            if proxy_server:
                ydl_opts['proxy'] = proxy_server

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                filename = f"{info.get('title', 'audio')}.mp3"

                buffer = io.BytesIO()
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_downloader:
                    original_stdout = sys.stdout
                    sys.stdout = buffer
                    try:
                        ydl_downloader.download([video_url])
                    finally:
                        sys.stdout = original_stdout

                buffer.seek(0)
                return send_file(
                    buffer,
                    mimetype="audio/mpeg",
                    as_attachment=True,
                    download_name=filename
                )

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
