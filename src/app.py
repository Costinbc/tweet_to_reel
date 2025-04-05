from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    tweet_url = request.form.get("url")
    if not tweet_url:
        return jsonify({"error": "Missing tweet URL"}), 400

    tweet_id = tweet_url.split("/")[-1]
    job_id = str(uuid.uuid4())[:8]

    try:
        subprocess.run(["python", "src/screenshot.py", tweet_url], check=True)
        subprocess.run(["python", "src/extract_tweet_text.py", "tweet", f"downloads/{tweet_id}.png", f"downloads/{tweet_id}_cropped.png"], check=True)
        subprocess.run(["python", "src/extract_tweet_text.py", "author_and_text_only", f"downloads/{tweet_id}_cropped.png", f"results/{tweet_id}_final.png"], check=True)
        subprocess.run(["python", "src/video_dl.py", tweet_url], check=True)
        subprocess.run(["python", "src/assemble_reel.py", f"results/{tweet_id}_final.png", "tweet_video.mp4", f"results/{job_id}_reel.mp4"], check=True)

        return send_file(f"results/{job_id}_reel.mp4", as_attachment=True)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
