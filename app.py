import io
import os
import re
import tempfile
from flask import Flask, render_template, request, send_file
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

        # Generate a safe, unique temporary file footprint inside the system cache directory
        temp_dir = tempfile.gettempdir()
        temp_filepath = os.path.join(temp_dir, 'downloaded_track')

        try:
            # Configure yt-dlp to download directly to a temporary file path
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_filepath,
                'logtostderr': True,
                'quiet': True,
                'noplaylist': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract metadata to fetch the actual song title
                info = ydl.extract_info(media_url, download=True)
                clean_title = "".join([c for c in info.get('title', 'audio') if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                filename = f"{clean_title or 'track'}.mp3"

            # Locate the exact downloaded audio file extensions (.mp3, .ogg, etc.)
            actual_file = None
            for f in os.listdir(temp_dir):
                if f.startswith('downloaded_track'):
                    actual_file = os.path.join(temp_dir, f)
                    break

            if not actual_file or not os.path.exists(actual_file):
                return "The server failed to capture the audio download stream.", 500

            # Read the physical file into an isolated in-memory byte buffer
            return_data = io.BytesIO()
            with open(actual_file, 'rb') as f:
                return_data.write(f.read())
            return_data.seek(0)

            # Cleanup step: Instantly purge the file from the Render disk array
            try:
                os.remove(actual_file)
            except Exception:
                pass

            # Stream the file down as a secure attachment directly to the web browser
            return send_file(
                return_data,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            # Fallback error recovery routine to ensure the server never retains junk storage fragments
            for f in os.listdir(temp_dir):
                if f.startswith('downloaded_track'):
                    try:
                        os.remove(os.path.join(temp_dir, f))
                    except Exception:
                        pass
            return f"The server was unable to process this audio link. Details: <br>{str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
