from app.db import db
from datetime import datetime,timezone
note_leads = db.Table(
    "note_leads",
    db.Column(
        "note_leads",
        db.Integer,
        db.ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "lead_id",
        db.Integer,
        db.ForeignKey("leads.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class Lead(db.Model):
    __tablename__ = "leads"
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    source_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.Text, nullable=True)
    text = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=True)
    score = db.Column(db.Float, nullable=True)
    group_name = db.Column("group", db.String(100), nullable=True)
    best_profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"),nullable=True)
    match_explanation = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Float, nullable=True)


class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    stack = db.Column(db.Text, nullable=True)
    experience = db.Column(db.String(255),nullable=True)
    description=db.Column(db.Text, nullable=False)
    can_solve=db.Column(db.Text, nullable=True)
    url_resume = db.Column(db.Text)
    portfolio = db.Column(db.Text)
    success_score = db.Column(db.Float, nullable=True)

class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    profile = db.relationship("Profile")
    leads = db.relationship("Lead", secondary=note_leads)

class Repositories(db.Model):
    __tablename__="repositories"
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.BigInteger, unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    last_scanned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    issues = db.relationship("Issue",back_populates="repository",cascade="all, delete-orphan")

class Issue(db.Model):
    __tablename__ = "issues"
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.BigInteger, unique=True, nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey("repositories.id"),nullable=False)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=True)
    number = db.Column(db.BigInteger, nullable=False)
    html_url = db.Column(db.Text, nullable=False)
    repository=db.relationship("Repositories", back_populates="issues")
    comments=db.relationship("Comment", back_populates="issue", cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.BigInteger, unique=True, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=True)
    issue = db.relationship("Issue", back_populates="comments")

class IssueAnalysis(db.Model):
    __tablename__ = "issue_analyses"
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), unique=True, nullable=False)
    score = db.Column(db.Float, nullable=False)
    label = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    model_version = db.Column(db.String(100), nullable=False)

    issue = db.relationship("Issue")

class TrainingSample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), unique=True, nullable=False)
    score=db.Column(db.Float, nullable=False)
    text = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    issue = db.relationship("Issue")

class ProfileMatching(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), unique=True, nullable=False)
    best_profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=True)
    match_score = db.Column(db.Float, nullable=False)
    match_explanation = db.Column(db.Text, nullable=False)
    issue = db.relationship("Issue")
    profile = db.relationship("Profile")

class Finded(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String(100), nullable=False)
    priznak = db.Column(db.String(100), nullable=False)

class AppSetting(db.Model):
    __tablename__ = "app_settings"
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255), nullable=False)