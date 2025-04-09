import json

from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import uuid
import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(base_dir, "templates")
downloads_dir = os.path.join(base_dir, "downloads")
results_dir = os.path.join(base_dir, "results")
src_dir = os.path.join(base_dir, "src")

print("RUNNING FROM:", os.getcwd())
print("BASE DIR:", base_dir)

os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

screenshot_py = os.path.join(src_dir, "screenshot_tp.py")
extract_py = os.path.join(src_dir, "extract_tweet_text.py")
video_dl_py = os.path.join(src_dir, "video_dl.py")
assemble_py = os.path.join(src_dir, "assemble_reel.py")

app = Flask(__name__, template_folder=template_dir, static_folder=os.path.join(base_dir, "static"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tweet_url = request.form.get("url")
        if not tweet_url:
            return render_template("index.html", error="Please enter a tweet URL")

        tweet_id = tweet_url.split("/")[-1]
        job_id = str(uuid.uuid4())[:8]

        img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
        img_final = os.path.join(results_dir, f"{tweet_id}_final.png")
        video_path = os.path.join(downloads_dir, f"{tweet_id}_video.mp4")
        reel_output = os.path.join(results_dir, f"{job_id}_reel.mp4")

        try:
            start_time = datetime.datetime.now()

            executor = ThreadPoolExecutor(max_workers=1)
            video_download = executor.submit(
                subprocess.run,
                ["python", video_dl_py, tweet_url],
                check=True
            )

            subprocess.run(["python", screenshot_py, tweet_url, img_raw], check=True)
            with open("progress.json", "w") as f:
                json.dump({"percent": 10}, f)

            subprocess.run([
                "python", extract_py,
                "crop_tweet",
                img_raw,
                img_final
            ], check=True)

            with open("progress.json", "w") as f:
                json.dump({"percent": 25}, f)

            video_download.result()
            with open("progress.json", "w") as f:
                json.dump({"percent": 50}, f)

            subprocess.run([
                "python", assemble_py,
                img_final,
                video_path,
                reel_output
            ], check=True)
            with open("progress.json", "w") as f:
                json.dump({"percent": 100}, f)

            duration = datetime.datetime.now() - start_time
            print(f"Time taken to process tweet to reel: {duration}", flush=True)

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