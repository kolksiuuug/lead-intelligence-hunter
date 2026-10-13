from app.db import db
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
    __table_args__ = (
            db.UniqueConstraint("source","source_id", name="uq_leads_source_source_id"),
        )
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

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    stack = db.Column(db.Text, nullable=False)
    experience = db.Column(db.String(255),nullable=False)
    description=db.Column(db.Text, nullable=False)
    can_solve=db.Column(db.Text, nullable=False)
    url_resume = db.Column(db.Text)
    portfolio = db.Column(db.Text)
    success_score = db.Column(db.Float, nullable=False)

class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    profile = db.relationship("Profile")
    leads = db.relationship("Lead", secondary=note_leads)