import json
import os
import subprocess
import time
import uuid
import datetime
import requests
import logging
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google import auth
from flask import Flask, jsonify, render_template, request, send_file, make_response, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_root = os.getenv("T2R_DATA_DIR", "/tmp/t2r")
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")
downloads_dir = os.path.join(data_root, "downloads")
results_dir = os.path.join(data_root, "results")
src_dir = os.path.join(base_dir, "src")

os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

BUCKET = os.environ.get("STORAGE_BUCKET_NAME")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID")
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")

for name in ("STORAGE_BUCKET_NAME", "RUNPOD_ENDPOINT_ID", "RUNPOD_API_KEY",
             "AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "SECRET_KEY"):
    if not os.getenv(name):
        raise RuntimeError(f"Missing env var {name}")

storage_client = storage.Client()

screenshot_py = os.path.join(src_dir, "screenshot_ors.py")
crop_py = os.path.join(src_dir, "crop_tweet.py")
video_dl_py = os.path.join(src_dir, "video_dl.py")
assemble_py = os.path.join(src_dir, "assemble_reel.py")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(base_dir, 'app.db')}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from models import db, User, Job
db.init_app(app)
migrate = Migrate(app, db)

oauth = OAuth(app)
auth0 = oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)

executor = ThreadPoolExecutor(max_workers=4)

step_weights = {
    "start": 1,
    "screenshot": 5,
    "crop": 1,
    "video": 1,
    "reel": 4,
    "done": 1,
}


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user() -> User | None:
    user_info = session.get("user")
    if not user_info:
        return None
    return db.session.execute(
        db.select(User).filter_by(sub=user_info["sub"])
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/login")
def login():
    return auth0.authorize_redirect(redirect_uri=url_for("callback", _external=True))


@app.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    user_info = token["userinfo"]
    session["user"] = user_info

    user = db.session.execute(
        db.select(User).filter_by(sub=user_info["sub"])
    ).scalar_one_or_none()

    if not user:
        user = User(
            sub=user_info["sub"],
            email=user_info.get("email"),
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )
        db.session.add(user)
    else:
        user.email = user_info.get("email")
        user.name = user_info.get("name")
        user.picture = user_info.get("picture")
        user.last_login_at = datetime.datetime.utcnow()

    db.session.commit()
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{AUTH0_DOMAIN}/v2/logout"
        f"?returnTo={url_for('index', _external=True)}"
        f"&client_id={AUTH0_CLIENT_ID}"
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = current_user()
    if request.method == "POST":
        user.default_output_type = request.form.get("default_output_type", "photo")
        user.default_background = request.form.get("default_background", "white")
        user.default_layout = request.form.get("default_layout", "video_bottom")
        db.session.commit()
        return redirect(url_for("settings"))
    return render_template("settings.html", user=user)


# ---------------------------------------------------------------------------
# GCS / RunPod helpers
# ---------------------------------------------------------------------------

def _signed_urls(tweet_id: str, layout: str, background: str, cropped: bool):
    reel_cropped = "cropped" if cropped else "uncropped"
    filename = f"{tweet_id}_{layout}_{background}_{reel_cropped}.mp4"
    obj = (
        f"reels/{datetime.date.today():%Y/%m/%d}/"
        f"{tweet_id}_{layout}_{background}_{reel_cropped}.mp4"
    )

    SCOPES = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/iam"
    ]

    credentials, project = auth.default(scopes=SCOPES)
    credentials.refresh(auth.transport.requests.Request())

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(obj)

    upload_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
        method="PUT",
        content_type="video/mp4")

    public_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=1),
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
        method="GET",
        response_type="video/mp4",
        response_disposition=f'attachment; filename="{filename}"'
    )

    return upload_url, public_url, obj


def _wait_for_runpod(result_id: str, public_url: str, job_id: str):
    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{result_id}"
    headers    = {"Authorization": RUNPOD_API_KEY}

    while True:
        output = ""
        try:
            r = requests.get(status_url, headers=headers, timeout=15)
            r.raise_for_status()
            state = r.json()["status"]
            if not output:
                output = r.json().get("output", {})
        except Exception as e:
            state = f"ERROR: {e}"

        if state == "COMPLETED":
            write_progress(job_id, {
                "status": "Reel created.",
                "step":   "done",
                "redirect_url": f"/result/reel/{job_id}",
                "public_url": public_url,
            })
            break

        elif state in ("FAILED", "CANCELLED") or state.startswith("ERROR"):
            write_progress(job_id, {
                "status": f"job {state}",
                "step":   "error",
            })
            break
        else:
            if output:
                start_time = load_progress(job_id).get("start_time", time.time())
                estimated_time = output.split("Estimated time:")[-1].strip().split(" ")[0]
                time_left = int(round((float(estimated_time)) - int(time.time() - start_time)))
                write_progress(job_id, {
                    "status": f"Processing video…",
                    "start_time": start_time,
                    "step":   "video",
                    "time_left": time_left,
                })
            else:
                if state == "IN_PROGRESS":
                    write_progress(job_id, {
                        "status": f"Processing video…",
                        "step":   "video",
                    })
                elif state == "IN_QUEUE":
                    write_progress(job_id, {
                        "status": f"job queued…",
                        "step":   "queue",
                    })


def progress_path(job_id: str) -> str:
    return os.path.join(base_dir, f"progress_{job_id}.json")

def write_progress(job_id: str, data: dict):
    with open(progress_path(job_id), "w") as f:
        json.dump(data, f)

def load_progress(job_id: str):
    try:
        with open(progress_path(job_id)) as f:
            return json.load(f)
    except Exception:
        return {}


def call_handler(job_id: str, tweet_url: str, only_video: str, layout: str, hide_quoted_tweet: str, background: str, cropped: bool):
    upload_url, public_url, obj = _signed_urls(tweet_url.split("/")[-1], layout, background, cropped)

    data = {
        "input": {
            "upload_url": upload_url,
            "public_url": public_url,
            "tweet_url": tweet_url,
            "only_video": only_video,
            "layout": layout,
            "hide_quoted_tweet": hide_quoted_tweet,
            "background": background,
            "cropped": cropped
            },
    }

    r = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
        headers={"Authorization": RUNPOD_API_KEY},
        json=data, timeout=30)
    r.raise_for_status()
    return r.json()["id"], public_url


def process_job(tweet_url: str, type: str, layout: str, only_video: str, show_replied_to_tweet: str, hide_quoted_tweet: str, background: str, cropped: bool, job_id: str, user_sub: str):
    tweet_id = tweet_url.rstrip("/").split("/")[-1].split("?")[0]
    img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
    img_cropped = os.path.join(downloads_dir, f"{tweet_id}_cropped.png")
    img_final = os.path.join(results_dir, f"{job_id}_photo.png")

    start_time = time.time()
    write_progress(job_id, {
        "status": "Starting...",
        "step": "start",
        "start_time": start_time,
        "video_duration": 0,
        "type": type,
        "layout": layout,
        "only_video": only_video,
        "show_replied_to_tweet": show_replied_to_tweet,
        "hide_quoted_tweet": hide_quoted_tweet,
        "background": background,
        "cropped": cropped,
    })

    with app.app_context():
        db_job = Job(
            job_uuid=job_id,
            user_sub=user_sub,
            tweet_url=tweet_url,
            kind=type,
            status="processing",
        )
        db.session.add(db_job)
        db.session.commit()

    if type == "video":
        try:
            logging.info("Starting VIDEO job %s", job_id)
            result_id, public_url = call_handler(job_id, tweet_url, only_video, layout, hide_quoted_tweet, background, cropped)
            logging.info("RunPod job %s enqueued url=%s", result_id, public_url)
            write_progress(job_id, {
                "status": "Job queued",
                "step": "video",
            })
            _wait_for_runpod(result_id, public_url, job_id)
            with app.app_context():
                j = db.session.execute(db.select(Job).filter_by(job_uuid=job_id)).scalar_one_or_none()
                if j:
                    j.status = "done"
                    j.result_url = public_url
                    db.session.commit()
        except Exception as e:
            logging.exception("Job %s failed: %s", job_id, e)
            write_progress(job_id, {
                "status": "ERROR: " + str(e),
                "step": "error"
            })
            with app.app_context():
                j = db.session.execute(db.select(Job).filter_by(job_uuid=job_id)).scalar_one_or_none()
                if j:
                    j.status = "error"
                    db.session.commit()

    else:
        write_progress(job_id, {
            "status": "Downloading image...",
            "step": "screenshot",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", screenshot_py, "photo", show_replied_to_tweet, hide_quoted_tweet, background, tweet_url, img_raw], check=True)

        write_progress(job_id, {
            "status": "Cropping image...",
            "step": "crop",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", crop_py, "photo_card", img_raw, img_cropped], check=True)

        write_progress(job_id, {
            "status": "Padding image...",
            "step": "pad",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", crop_py, "pad_photo", background, img_cropped, img_final], check=True)

        write_progress(job_id, {
            "status": "Image created.",
            "step": "done",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
            "redirect_url": f"/result/photo/{job_id}",
        })
        with app.app_context():
            j = db.session.execute(db.select(Job).filter_by(job_uuid=job_id)).scalar_one_or_none()
            if j:
                j.status = "done"
                db.session.commit()


# ---------------------------------------------------------------------------
# Main routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    user = current_user()
    if request.method == "POST":
        tweet_url = request.form.get("url")
        type = request.form.get("type")
        only_video = request.form.get("only_video") if type == "video" else 'false'
        layout = request.form.get("layout") if only_video == 'false' else 'video_only'
        show_replied_to_tweet = request.form.get("show_replied_to_tweet") if type == "photo" else 'false'
        if type == "photo":
            hide_quoted_tweet = request.form.get("hide_quoted_tweet_photo", "false")
        elif type == "video" and only_video == 'false':
            hide_quoted_tweet = request.form.get("hide_quoted_tweet_video", "false")
        else:
            hide_quoted_tweet = 'false'
        background = request.form.get("background-photo") if type == "photo" else request.form.get("background-video")
        cropped = request.form.get("cropped") == "1"

        if not tweet_url:
            if request.headers.get("HX-Request"):
                resp = make_response(render_template("index.html", error="Please enter a tweet URL", user=user))
                resp.headers["Cache-Control"] = "no-store"
                return resp
            return jsonify(error="Please enter a tweet URL"), 400

        job_id = uuid.uuid4().hex[:8]
        executor.submit(process_job, tweet_url, type, layout, only_video, show_replied_to_tweet, hide_quoted_tweet, background, cropped, job_id, user.sub if user else None)

        if request.headers.get("HX-Request"):
            resp = make_response(render_template("partials/queued.html", job_id=job_id))
            resp.headers["Cache-Control"] = "no-store"
            return resp

        return jsonify(job_id=job_id, type=type, layout=layout, only_video=only_video, show_replied_to_tweet=show_replied_to_tweet,
                       hide_quoted_tweet=hide_quoted_tweet, background=background, cropped=cropped), 202

    return render_template("index.html", user=user)


@app.route("/result/reel/<job_id>")
def reel_result(job_id):
    data = load_progress(job_id)
    return render_template("download_reel.html", gcs_url=data.get("public_url"))


@app.route("/result/photo/<job_id>")
def photo_result(job_id):
    return render_template("download_photo.html", filename=f"{job_id}_photo.png")


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(results_dir, filename), as_attachment=True)


@app.route("/health")
def health():
    return "ok", 200


@app.route("/progress-frag")
def progress_frag():
    job_id = request.args.get("job_id")

    def no_cache(resp):
        resp.headers["Cache-Control"] = "no-store"
        return resp

    if not job_id:
        return no_cache(make_response(render_template(
            "partials/progress.html",
            job_id="", status="Waiting…", time_left="-", percent=0, show_preview=False
        )))

    data = load_progress(job_id) or {}
    status     = data.get("status", "Working…")
    start_time = data.get("start_time", time.time())
    video_dur  = data.get("video_duration", 0)
    type_      = data.get("type", "video")
    step = data.get("step", "start")
    time_left = data.get("time_left", "~")

    base = dict(step_weights)
    if type_ == "photo":
        base["reel"] = 0
        base["video"] = 0
    else:
        base["reel"] = int(video_dur * 0.9) if video_dur else 0

    if step == 'video':
        base_percentage = 30
    else:
        base_percentage = 5

    elapsed = max(time.time() - start_time, 0)
    if time_left != "~" and int(time_left) > 0:
        est_total = elapsed + int(time_left)
    else:
        est_total = 25
    percent = base_percentage + min(int((elapsed / est_total) * 100), 95 - base_percentage)

    redirect_url = data.get("redirect_url")
    if redirect_url:
        resp = make_response("")
        resp.headers["HX-Redirect"] = redirect_url
        return no_cache(resp)

    return no_cache(make_response(render_template(
        "partials/progress.html",
        job_id=job_id,
        status=status,
        time_left=data.get("time_left", "~"),
        percent=percent,
        show_preview=True
    )))


@app.route("/instructions")
def how_it_works():
    return render_template("instructions.html")


@app.after_request
def add_cache_headers(resp):
    if request.path.startswith("/static/") and "styles.css" in request.path:
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
