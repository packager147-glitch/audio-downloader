import io
import os
from flask import Flask, render_template, request, Response
from pytubefix import YouTube
from pytubefix.cli import on_progress

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("url")
        if not video_url:
            return "Please provide a valid URL.", 400

        try:
            # Initialize connection using the modern pytubefix client layout
            yt = YouTube(video_url, on_progress_callback=on_progress)
            
            # Extract the raw, high-bitrate audio stream track
            audio_stream = yt.streams.get_audio_only()
            if not audio_stream:
                return "No playable audio stream detected on this video.", 404
                
            # Safely generate an attachment file name string
            clean_title = "".join([c for c in yt.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{clean_title or 'audio'}.mp3"

            # Stream the media track directly into memory to bypass Render storage blocks
            buffer = io.BytesIO()
            audio_stream.stream_to_buffer(buffer)
            buffer.seek(0)

            # Generate binary payload to send straight to browser download
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
            # Gracefully catch validation failures without a hard crash
            return f"The server is unable to process this video link. Details: <br>{str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
