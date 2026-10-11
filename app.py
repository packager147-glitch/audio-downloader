import io
import os
import re
from flask import Flask, render_template, request, Response
import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        media_url = request.form.get("url")
        if not media_url:
            return "Please provide a valid URL.", 400

        # Validate that the link is a valid SoundCloud URL
        if not re.search(r'(soundcloud\.com|snd\.sc)', media_url):
            return "Error: This application currently supports SoundCloud tracks only.", 400

        try:
            # Configure yt-dlp to stream audio from SoundCloud into server memory
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '-',  # Directly streams raw chunks to stdout
                'logtostderr': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract metadata to fetch the actual song title
                info = ydl.extract_info(media_url, download=False)
                clean_title = "".join([c for c in info.get('title', 'audio') if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                filename = f"{clean_title or 'track'}.mp3"

                # Instantiate the real-time download into a memory buffer
                buffer = io.BytesIO()
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_downloader:
                    import sys
                    original_stdout = sys.stdout
                    sys.stdout = buffer
                    try:
                        ydl_downloader.download([media_url])
                    finally:
                        sys.stdout = original_stdout

                buffer.seek(0)

                # Stream the chunks straight to the browser
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
            return f"The server was unable to process this audio link. Details: <br>{str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
