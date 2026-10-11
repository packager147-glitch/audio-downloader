import io
from flask import Flask, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("url")
        if not video_url:
            return "Please provide a valid URL.", 400

        try:
            # Configure yt-dlp to extract audio in memory without saving a local file
                        # Configure yt-dlp to bypass bot blocks via mobile client spoofing
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '-',  # Outputs directly to stdout
                'logtostderr': True,
                'quiet': True,
                # Force yt-dlp to bypass data center blocks using modern extractor arguments
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],
                        'skip': ['webpage', 'configs'],
                    }
                },
                # Adjust HTTP headers to look identical to an Apple iPhone
                'http_headers': {
                    'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X; en_US)',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            }



            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video metadata first to get the title
                info = ydl.extract_info(video_url, download=False)
                filename = f"{info.get('title', 'audio')}.mp3"

                # Download the stream into an in-memory byte buffer
                buffer = io.BytesIO()
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_downloader:
                    # Redirect stdout to our buffer
                    import sys
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
    app.run(host="0.0.0.0", port=5000)
