import json

from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
import subprocess
import os
import uuid
import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(base_dir, "templates")
downloads_dir = os.path.join(base_dir, "downloads")
results_dir = os.path.join(base_dir, "results")

print("RUNNING FROM:", os.getcwd())
print("BASE DIR:", base_dir)

os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

app = Flask(__name__, template_folder=template_dir, static_folder=os.path.join(base_dir, "static"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tweet_url = request.form.get("url")
        if not tweet_url:
            return render_template("index.html", error="Please enter a tweet URL")

        tweet_id = tweet_url.split("/")[-1]
        job_id = str(uuid.uuid4())[:8]

        try:
            time = datetime.datetime.now()
            subprocess.run(["python", os.path.join("src", "screenshot_ors.py"), tweet_url], check=True)
            with open("progress.json", "w") as f:
                json.dump({"percent": 10}, f)

            subprocess.run([
                "python", os.path.join("src", "extract_tweet_text.py"),
                "tweet_card",
                os.path.join(downloads_dir, f"{tweet_id}.png"),
                os.path.join(results_dir, f"{tweet_id}_final.png")
            ], check=True)

            with open("progress.json", "w") as f:
                json.dump({"percent": 25}, f)

            subprocess.run(["python", os.path.join("src", "video_dl.py"), tweet_url], check=True)
            with open("progress.json", "w") as f:
                json.dump({"percent": 50}, f)

            subprocess.run([
                "python", os.path.join("src", "assemble_reel.py"),
                os.path.join(results_dir, f"{tweet_id}_final.png"),
                os.path.join(downloads_dir, f"{tweet_id}_video.mp4"),
                os.path.join(results_dir, f"{job_id}_reel.mp4")
            ], check=True)
            with open("progress.json", "w") as f:
                json.dump({"percent": 100}, f)

            print(f"Time taken {datetime.datetime.now() - time}")

            return redirect(url_for("result", job_id=job_id))

        except subprocess.CalledProcessError as e:
            return render_template("index.html", error="Something went wrong during processing.")

    return render_template("index.html")

@app.route("/result/<job_id>")
def result(job_id):
    filename = f"{job_id}_reel.mp4"
    return render_template("download.html", filename=filename)

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(results_dir, filename)
    return send_file(path, as_attachment=True)

@app.route("/health")
def health():
    return "✅ App is running!"

@app.route("/progress")
def progress():
    import json
    with open("progress.json", "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))