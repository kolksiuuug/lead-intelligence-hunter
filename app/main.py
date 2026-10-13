from sqlalchemy import or_
import os
from app.services.normalize import normalize_url
from flask import Flask
from flask_migrate import Migrate
from flask import request
from app.error_handlers.handler import error_handler
from flask import abort
from app.db import db
from app.models import Lead,Profile,Note
from app.services.lead_service import save_lead
from app.services.smart_parser import note_to_dict,lead_to_dict,profile_to_dict,get_columns_for_leads,get_colums_for_profile
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql+psycopg://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}@db:5432/{os.environ["POSTGRES_DB"]}'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
migrate = Migrate(app, db)
error_handler(app)

context = []

@app.route('/')
def home():
    return {"status":"ok", "message":"ai project already set"}
#http://127.0.0.1:5000/

@app.route("/leads", methods=["GET"])
def get_leads():
    leads = Lead.query.all()
    return [
        {"id": lead.id,
        "source": lead.source,
        "title": lead.title,
        "text": lead.text,
        "url": lead.url,
        "author": lead.author,
        "score": lead.score,
        "group": lead.group_name} for lead in leads
    ]
#http://127.0.0.1:5000/leads

@app.route('/leads', methods=["POST"])
def create_lead():
    data = request.get_json()
    lead,result = save_lead(data)
    if result["message"] == "lead was created": return lead_to_dict(lead), 201
    return {"message":f"лид с id:{lead_to_dict(lead)['id']} - был обновлен"}
    

r'''curl -X POST http://127.0.0.1:5000/leads \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "reddit_123",
    "text": "I am looking for a security monitoring tool",
    "url": "https://reddit.com/example",
    "author": "test_user",
    "source": "reddit",
    "title": "Looking for security tool",
    "score": 0.85,              
    "group":"3"
  }'''

@app.route('/leads/<int:lead_id>')
def get_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if lead is None: abort(404)
    return lead_to_dict(lead)
#http://127.0.0.1:5000/leads/3

@app.route("/health")
def get_health():
    return {"ok": True}
#http://127.0.0.1:5000/health

@app.route('/leads/<int:lead_id>', methods=["PUT"])
def update_lead(lead_id):
    data = request.get_json()
    lead = db.session.get(Lead, lead_id)
    if lead is None: abort(404)
    lead.source_id = data.get("source_id", lead.source_id)
    lead.source = data.get("source", lead.source)
    lead.text = data.get("text", lead.text)
    lead.author = data.get("author", lead.author)
    lead.url = normalize_url(data.get("url", lead.url))
    lead.score = data.get("score", lead.score)
    lead.group_name = data.get("group", lead.group_name)
    lead.title = data.get("title", lead.title)
    db.session.commit()
    return lead_to_dict(lead), 200


r"""
curl -X PUT http://127.0.0.1:5000/leads/1 -H "Content-Type: application/json" -d '{"id":1,
    "source_id": "reddit_123",
    "text": "I am looking for a security monitoring tool",
    "url": "https://reddit.com/example",
    "author": "test_user",
    "source": "reddit",
    "title": "Looking for security tool",
    "score": 0.85,              
    "group":"5"
  }'
"""

@app.route('/leads/<int:lead_id>', methods=["DELETE"])
def delete_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if lead is None: abort(404)
    db.session.delete(lead)
    db.session.commit()
    return {"message":f"your lead {lead_id} was deleted"}, 200
#curl -X DELETE http://127.0.0.1:5000/leads/1

@app.route('/leads/search')
def search_leads():
    data = request.json()
    score = get_columns_for_leads(data)[-1]
    #ml reading i do for score but we need context too
    return 0
#no
#--------------------------------------------------------
@app.route('/filter', methods=["GET"])
def filter_leads_by_param():
    param = request.args.get('context')
    min_score = request.args.get("min_score", type=float)
    if param is None: return {"error":"bad request< there is not context param in url"}, 400
    query = Lead.query.filter(or_(Lead.source==param,Lead.group_name.ilike(f"%{param}%"), Lead.author.ilike(f"%{param}%"), Lead.text.ilike(f"%{param}%"), Lead.title.ilike(f"%{param}%"), Lead.url.ilike(f"%{param}%")))
    if min_score is not None:
        query = query.filter(Lead.score >= min_score)
    result = query.all()
    if not result: abort(404)
    return [lead_to_dict(lead) for lead in result], 200
#http://127.0.0.1:5000/filter?context=user123

@app.route('/profiles', methods=["GET"])
def get_profiles():
    profiles = Profile.query.all()
    if profiles is None: abort(404)
    return [profile_to_dict(profile) for profile in profiles], 200
#http://127.0.0.1:5000/profiles

@app.route('/profile/<int:profile_id>', methods=["GET"])
def get_profile(profile_id):
    profile = db.session.get(Profile, profile_id)
    if profile is None: abort(404)
    return profile_to_dict(profile), 200
#http://127.0.0.1:5000/profile/1

@app.route('/profile', methods=["POST"])
def create_profile():
    data = request.get_json()
    stack1,experience1,description1,can_solve1,url_resume1,portfolio1,success_score1 = get_colums_for_profile(data)
    profile = Profile(stack=stack1, experience=experience1, description=description1, can_solve=can_solve1, url_resume=normalize_url(url_resume1), portfolio=normalize_url(portfolio1), success_score=success_score1)
    db.session.add(profile)
    db.session.commit()
    return {"message":"your profile was written"}

r'''curl -X POST http://127.0.0.1:5000/profile \
  -H "Content-Type: application/json" \
  -d '{
    "stack": "Python, Data Science",
    "experience": "3 years",
    "description": "Data Scientist specializing in ML",
    "can_solve": "classification, regression, anomaly detection",
    "url_resume": "https://example.com/resume",
    "portfolio": "https://github.com/example",
    "success_score": 0.92
  }'''

@app.route('/profile/<int:profile_id>', methods=["DELETE"])
def delete_profile(profile_id):
    profile = db.session.get(Profile, profile_id)
    if profile is None: abort(404)
    db.session.delete(profile)
    db.session.commit()
    return {"message":"the profile was deleted"}
#curl -X DELETE http://127.0.0.1:5000/profile/3


@app.route('/profile/<int:profile_id>', methods=["PUT"])
def change_profile(profile_id):
    data = request.get_json()
    profile = db.session.get(Profile, profile_id)
    if profile is None: abort(404)
    profile.stack = data.get("stack", profile.stack)
    profile.experience = data.get("experience", profile.experience)
    profile.description = data.get("description", profile.description)
    profile.can_solve = data.get("can_solve", profile.can_solve)
    profile.url_resume = data.get("url_resume", profile.url_resume)
    profile.portfolio = data.get("portfolio", profile.portfolio)
    profile.success_score = data.get("success_score", profile.success_score)
    db.session.commit()
    return {"message":"your profile was updated"}

    
r'''curl -X PUT http://127.0.0.1:5000/profile/2 \
  -H "Content-Type: application/json" \
  -d '{"stack": "Pytdfdffdhon", "experience": "15 years"}'''

@app.route('/choose', methods=["POST"])
def choose_lead():
    data = request.get_json()
    global context
    if not isinstance(data, dict) or "id" not in data: abort(400)
    ipd = data["id"]
    lead = db.session.get(Lead, ipd)
    if lead is None or ipd in context: abort(400)
    context.append(ipd)
    return {"message":"selected"}, 200

r'''curl -X POST http://127.0.0.1:5000/choose \
  -H "Content-Type: application/json" \
  -d '[{"id": 1}, {"id": 2}]'''

@app.route('/share', methods=["POST"])
def share_leads():
    global context
    urls = []
    if not context: return {"message":"leads did not selected"}, 400
    for lead in context:
        urls.append(
            f'http://127.0.0.1:5000/leads/{lead}'
        )
    context = []
    return {"urls":urls}, 200
r'''curl -X POST http://127.0.0.1:5000/share \ 
  -H "Content-Type: application/json"
  -d '[{"id":1}]'''

@app.route('/notes', methods=["GET"])
def get_notes():
    notes = Note.query.all()
    if notes is None: abort(404)
    return [note_to_dict(note) for note in notes], 200
#http://127.0.0.1:5000/notes

@app.route('/notes/<int:note_id>', methods=["GET"])
def get_note_by_id(note_id):
    note = db.session.get(Note, note_id)
    if note is None: abort(404)
    return note_to_dict(note), 200
#http://127.0.0.1:5000/notes/1

@app.route('/notes', methods=["POST"])
def write_a_note():
    data = request.get_json()
    text1,purpose1,leads1,profile1=data.get("text"),data.get("purpose"),data.get("leads", []),data.get("profile")
    if not text1 or not purpose1 or not profile1: abort(400)
    profile = db.session.get(Profile, profile1)
    if profile is None: abort(400)
    leads = []
    for lead_id in leads1:
        lead = db.session.get(Lead, lead_id)
        if lead is None: abort(400)
        leads.append(lead)
    note = Note(text=text1, purpose=purpose1, leads=leads, profile=profile)
    db.session.add(note)
    db.session.commit()
    return {"message":"your note was written", "id":note.id}, 201
r"""curl -X POST http://127.0.0.1:5000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Позвонить потенциальному клиенту",
    "purpose": "Первичный контакт",
    "leads": [1, 2],
    "profile": 1
  }'"""

@app.route('/notes/<int:note_id>', methods=["DELETE"])
def complete_note(note_id):
    note = db.session.get(Note, note_id)
    if note is None: abort(404)
    db.session.delete(note)
    db.session.commit()
    return {"message":"your note was completed"}
#curl -X DELETE http://127.0.0.1:5000/notes/1

@app.route('/notes/<int:note_id>', methods=["PUT"])
def change_note(note_id):
    data = request.get_json()
    note = db.session.get(Note, note_id)
    if note is None: abort(404)
    note.text = data.get("text", note.text)
    note.purpose = data.get("purpose", note.purpose)
    if "profile" in data: profile=db.session.get(Profile, data["profile"])
    if profile is None: abort(400)
    note.profile = profile
    if "leads" in data:
        selected_leads = Lead.query.filter(Lead.id.in_(data["leads"])).all()
        if len(selected_leads) != len(set(data["leads"])):
            abort(404)
        note.leads = selected_leads
    db.session.commit()
    return {"message":"your note was edited"}
r"""curl -X PUT http://127.0.0.1:5000/notes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Обновленный текст",
    "purpose": "Новый purpose",
    "leads": [2, 3],
    "profile": 1
  }'"""


@app.route('/stats')
def get_all_stats():
    count_leads,count_profiles,count_notes=db.session.query(Lead).count(),db.session.query(Profile).count(),db.session.query(Note).count()
    return {"leads":count_leads, "profiles":count_profiles, "notes":count_notes}
#http://127.0.0.1/stats

if __name__ == "__main__":
    app.run(debug=True)