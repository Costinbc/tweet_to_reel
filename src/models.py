from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), index=True)
    name = db.Column(db.String(255))
    picture = db.Column(db.String(512))
    stripe_customer_id = db.Column(db.String(255))
    plan = db.Column(db.String(64), default="free")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    # Per-user default settings
    default_output_type = db.Column(db.String(20), default="photo")
    default_background = db.Column(db.String(20), default="white")
    default_layout = db.Column(db.String(20), default="video_bottom")

    jobs = db.relationship("Job", backref="user", lazy=True, foreign_keys="Job.user_sub",
                           primaryjoin="User.sub == Job.user_sub")

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_uuid = db.Column(db.String(8), unique=True, index=True)
    user_sub = db.Column(db.String(255), db.ForeignKey("user.sub"), index=True, nullable=False)
    tweet_url = db.Column(db.Text)
    kind = db.Column(db.String(20))
    status = db.Column(db.String(20))
    result_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
