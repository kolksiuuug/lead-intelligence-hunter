from sqlalchemy import or_
import os
from flask import Flask, request, abort, jsonify
from flask_migrate import Migrate
from app.error_handlers.handler import error_handler
from app.services.normalize import normalize_url
from app.services.validation import validate_lead
from app.db import db
from app.models import (
    Lead, Profile, Note, Repositories, Issue, Comment,
    IssueAnalysis, TrainingSample, ProfileMatching, AppSetting, Finded
)
from app.services.llm_service import get_selected_provider, get_available_providers
from app.services.lead_service import save_lead
from app.services.smart_parser import *
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql+psycopg://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}@db:5432/{os.environ["POSTGRES_DB"]}'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
migrate = Migrate(app, db)
error_handler(app)

context = []

@app.route('/')
def home():
    return {"status": "ok", "message": "ai project already set"}


@app.route("/leads", methods=["GET"])
def get_leads():
    leads = Lead.query.all()
    return [lead_to_dict(lead) for lead in leads], 200


@app.route('/leads', methods=["POST"])
def create_lead():
    data = request.get_json(silent=True)
    validate_lead(data)
    lead, result = save_lead(data)
    if result["message"] == "lead was created":
        return lead_to_dict(lead), 201
    return {"message": f"лид с id:{lead.id} - был обновлен"}, 200


@app.route('/leads/<int:lead_id>', methods=["GET"])
def get_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)
    return lead_to_dict(lead), 200


@app.route("/health", methods=["GET"])
def get_health():
    return {"ok": True}, 200


@app.route('/leads/<int:lead_id>', methods=["PUT"])
def update_lead(lead_id):
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)

    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)

    if "source_id" in data:
        lead.source_id = data["source_id"]
    if "source" in data:
        lead.source = data["source"]
    if "text" in data:
        lead.text = data["text"]
    if "author" in data:
        lead.author = data["author"]
    if "url" in data:
        lead.url = normalize_url(data["url"]) if data["url"] else data["url"]
    if "score" in data:
        if data["score"] is not None and (
            type(data["score"]) not in (int, float)
            or not 0 <= data["score"] <= 1
        ):
            abort(400)
        lead.score = data["score"]
    if "group" in data:
        lead.group_name = data["group"]
    if "title" in data:
        lead.title = data["title"]

    db.session.commit()
    return lead_to_dict(lead), 200


@app.route('/leads/<int:lead_id>', methods=["DELETE"])
def delete_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)
    db.session.delete(lead)
    db.session.commit()
    return {"message": f"your lead {lead_id} was deleted"}, 200


@app.route('/leads/search', methods=["GET"])
def search_leads():
    param = request.args.get("context")
    min_score = request.args.get("min_score", type=float)

    if not param:
        abort(400)

    query = Lead.query.filter(
        or_(
            Lead.source == param,
            Lead.source_id == param,
            Lead.group_name.ilike(f"%{param}%"),
            Lead.author.ilike(f"%{param}%"),
            Lead.text.ilike(f"%{param}%"),
            Lead.title.ilike(f"%{param}%"),
            Lead.url.ilike(f"%{param}%")
        )
    )

    if min_score is not None:
        if not 0 <= min_score <= 1:
            abort(400)
        query = query.filter(Lead.score >= min_score)

    leads = query.all()
    return [lead_to_dict(lead) for lead in leads], 200

@app.route("/repositories", methods=["GET"])
def get_repositories():
    repositories = Repositories.query.order_by(Repositories.id.desc()).all()
    return jsonify([repository_to_dict(repository, include_issues=False) for repository in repositories])


@app.route("/repositories/<int:repository_id>", methods=["GET"])
def get_repository(repository_id):
    repository = db.session.get(Repositories, repository_id)
    if repository is None:
        abort(404)
    return jsonify(repository_to_dict(repository))


@app.route("/issues/<int:issue_id>", methods=["GET"])
def get_issue(issue_id):
    issue = db.session.get(Issue, issue_id)
    if issue is None:
        abort(404)
    return jsonify(issue_to_dict(issue))


@app.route("/issues/<int:issue_id>/comments", methods=["GET"])
def get_issue_comments(issue_id):
    issue = db.session.get(Issue, issue_id)
    if issue is None:
        abort(404)
    return jsonify([comment_to_dict(comment) for comment in issue.comments])


@app.route("/issues/<int:issue_id>/analysis", methods=["GET"])
def get_issue_analysis(issue_id):
    issue = db.session.get(Issue, issue_id)
    if issue is None:
        abort(404)

    analysis = IssueAnalysis.query.filter_by(issue_id=issue_id).first()
    if analysis is None:
        return jsonify({"message": "analysis not found"}), 404

    return jsonify(issue_analysis_to_dict(analysis))


@app.route("/profile-matching", methods=["GET"])
def get_profile_matchings():
    matchings = ProfileMatching.query.order_by(ProfileMatching.id.desc()).all()
    return jsonify([profile_matching_to_dict(matching) for matching in matchings])


@app.route("/training-samples", methods=["GET"])
def get_training_samples():
    samples = TrainingSample.query.order_by(TrainingSample.id.desc()).all()
    return jsonify([training_sample_to_dict(sample) for sample in samples])


@app.route("/app-settings", methods=["GET"])
def get_app_settings():
    settings = AppSetting.query.order_by(AppSetting.key).all()
    return jsonify([app_setting_to_dict(setting) for setting in settings])


@app.route("/finded", methods=["GET"])
def get_finded():
    records = Finded.query.order_by(Finded.id.desc()).all()
    return jsonify([finded_to_dict(record) for record in records])

@app.route("/filter", methods=["GET"])
def filter_leads_by_param():
    param = request.args.get("context")
    min_score = request.args.get("min_score", type=float)

    if not param:
        return {"error": "there is no context param in url"}, 400

    query = Lead.query.filter(
        or_(
            Lead.source == param,
            Lead.group_name.ilike(f"%{param}%"),
            Lead.author.ilike(f"%{param}%"),
            Lead.text.ilike(f"%{param}%"),
            Lead.title.ilike(f"%{param}%"),
            Lead.url.ilike(f"%{param}%")
        )
    )

    if min_score is not None:
        if not 0 <= min_score <= 1:
            abort(400)
        query = query.filter(Lead.score >= min_score)

    result = query.all()
    return [lead_to_dict(lead) for lead in result], 200


@app.route('/profiles', methods=["GET"])
def get_profiles():
    profiles = Profile.query.all()
    return [profile_to_dict(profile) for profile in profiles], 200


@app.route('/profile/<int:profile_id>', methods=["GET"])
def get_profile(profile_id):
    profile = db.session.get(Profile, profile_id)
    if profile is None:
        abort(404)
    return profile_to_dict(profile), 200


@app.route('/profile', methods=["POST"])
def create_profile():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)

    stack1, experience1, description1, can_solve1, url_resume1, portfolio1, success_score1 = get_colums_for_profile(data)

    if type(success_score1) not in (int, float) or not 0 <= success_score1 <= 1:
        abort(400)

    profile = Profile(
        stack=stack1,
        experience=experience1,
        description=description1,
        can_solve=can_solve1,
        url_resume=normalize_url(url_resume1) if url_resume1 else None,
        portfolio=normalize_url(portfolio1) if portfolio1 else None,
        success_score=success_score1
    )

    db.session.add(profile)
    db.session.commit()
    return profile_to_dict(profile), 201


@app.route('/profile/<int:profile_id>', methods=["DELETE"])
def delete_profile(profile_id):
    profile = db.session.get(Profile, profile_id)
    if profile is None:
        abort(404)

    if Note.query.filter_by(profile_id=profile_id).first():
        return {"error": "profile is used by notes"}, 409

    db.session.delete(profile)
    db.session.commit()
    return {"message": "the profile was deleted"}, 200


@app.route('/profile/<int:profile_id>', methods=["PUT"])
def change_profile(profile_id):
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)

    profile = db.session.get(Profile, profile_id)
    if profile is None:
        abort(404)

    if "stack" in data:
        profile.stack = data["stack"]
    if "experience" in data:
        profile.experience = data["experience"]
    if "description" in data:
        profile.description = data["description"]
    if "can_solve" in data:
        profile.can_solve = data["can_solve"]
    if "url_resume" in data:
        profile.url_resume = normalize_url(data["url_resume"]) if data["url_resume"] else None
    if "portfolio" in data:
        profile.portfolio = normalize_url(data["portfolio"]) if data["portfolio"] else None
    if "success_score" in data:
        score = data["success_score"]
        if type(score) not in (int, float) or not 0 <= score <= 1:
            abort(400)
        profile.success_score = score

    db.session.commit()
    return profile_to_dict(profile), 200


@app.route('/choose', methods=["POST"])
def choose_lead():
    data = request.get_json()
    if not isinstance(data, dict) or "id" not in data:
        abort(400)

    lead_id = data["id"]
    if type(lead_id) is not int:
        abort(400)

    lead = db.session.get(Lead, lead_id)
    if lead is None:
        abort(404)

    if lead_id in context:
        return {"message": "lead already selected"}, 409

    context.append(lead_id)
    return {"message": "selected", "id": lead_id}, 200


@app.route('/share', methods=["POST"])
def share_leads():
    global context

    if not context:
        return {"message": "leads did not selected"}, 400

    urls = [
        f'{request.url_root.rstrip("/")}/leads/{lead_id}'
        for lead_id in context
    ]

    context = []
    return {"urls": urls}, 200


@app.route('/notes', methods=["GET"])
def get_notes():
    notes = Note.query.all()
    return [note_to_dict(note) for note in notes], 200


@app.route('/notes/<int:note_id>', methods=["GET"])
def get_note_by_id(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        abort(404)
    return note_to_dict(note), 200


@app.route('/notes', methods=["POST"])
def write_a_note():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)

    text1 = data.get("text")
    purpose1 = data.get("purpose")
    leads1 = data.get("leads", [])
    profile1 = data.get("profile")

    if not text1 or not purpose1 or profile1 is None:
        abort(400)
    if not isinstance(leads1, list):
        abort(400)
    if type(profile1) is not int:
        abort(400)

    profile = db.session.get(Profile, profile1)
    if profile is None:
        abort(404)

    leads = []
    for lead_id in leads1:
        if type(lead_id) is not int:
            abort(400)
        lead = db.session.get(Lead, lead_id)
        if lead is None:
            abort(404)
        leads.append(lead)

    note = Note(
        text=text1,
        purpose=purpose1,
        leads=leads,
        profile=profile
    )

    db.session.add(note)
    db.session.commit()
    return note_to_dict(note), 201


@app.route('/notes/<int:note_id>', methods=["DELETE"])
def complete_note(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        abort(404)

    db.session.delete(note)
    db.session.commit()
    return {"message": "your note was deleted"}, 200


@app.route('/notes/<int:note_id>', methods=["PUT"])
def change_note(note_id):
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)

    note = db.session.get(Note, note_id)
    if note is None:
        abort(404)

    if "text" in data:
        note.text = data["text"]
    if "purpose" in data:
        note.purpose = data["purpose"]

    if "profile" in data:
        profile_id = data["profile"]
        if type(profile_id) is not int:
            abort(400)

        profile = db.session.get(Profile, profile_id)
        if profile is None:
            abort(404)
        note.profile = profile

    if "leads" in data:
        leads1 = data["leads"]
        if not isinstance(leads1, list):
            abort(400)

        leads = []
        for lead_id in leads1:
            if type(lead_id) is not int:
                abort(400)
            lead = db.session.get(Lead, lead_id)
            if lead is None:
                abort(404)
            leads.append(lead)

        if len({lead.id for lead in leads}) != len(leads):
            abort(400)

        note.leads = leads

    db.session.commit()
    return note_to_dict(note), 200



@app.route('/stats')
def get_all_stats():
    count_leads,count_profiles,count_notes=db.session.query(Lead).count(),db.session.query(Profile).count(),db.session.query(Note).count()
    return {"leads":count_leads, "profiles":count_profiles, "notes":count_notes}
#http://127.0.0.1/stats

@app.route('/context_provider', methods=["GET", "PUT"])
def get_provider():
    if request.method == "GET":
        return jsonify({"provider":get_selected_provider(), "available":get_available_providers()})
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        provider = data.get("provider")
        if provider not in get_available_providers():
            abort(400)
        setting = AppSetting.query.filter_by(key="llm_provider").first()
        if setting is None:
            setting = AppSetting(key="llm_provider", value=provider)
            db.session.add(setting)
        else: setting.value = provider
    else: abort(400)
    db.session.commit()
    return jsonify({"provider":provider, "available":get_available_providers()})

if __name__ == "__main__":
    app.run(debug=True)