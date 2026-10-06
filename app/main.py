from flask import Flask
from flask import request
from error_handlers.handler import error_handler
from flask import abort
app = Flask(__name__)
error_handler(app)

leads = [{
  "id": 1,
  "source": "reddit",
  "source_id": "abc123",
  "title": "Someone is looking for a security tool",
  "text": "I need a tool that...",
  "url": "https://example.com/post/123",
  "author": "user123",
  "score": 0.87,
  "group":"2"
  },
  {
  "id": 2,
  "source": "fff",
  "source_id": "sss",
  "title": "security new",
  "text": "I need a lang that...",
  "url": "https://example.com/post/433",
  "author": "user33323",
  "score": 0.27,
  "group":"1"
  },
  {
    "id": 3,
    "source": "fff",
    "source_id": "dfd",
    "title": "dfggfd",
    "text": "fgdgdf",
    "url": "fdgdgf",
    "author": "23232",
    "score": 0.17,
    "group":"1"
    }
]

profiles = [{
  "id": 1,
  "stack": "Javascript",
  "experience": "1 year",
  "description": "new_subject",
  "can_solve": "all ml problems",
  "url_resume": "https://example.com/resume",
  "portfolio": "hackerone_cases",
  "success_score": 0.60
  },
  {
  "id": 2,
  "stack": "PHP",
  "experience": "7 years",
  "description": "old_expert",
  "can_solve": "backend problems",
  "url_resume": "https://hello.com/resume_main",
  "portfolio": "avito_expert",
  "success_score": 0.90
  }
]


def find_max_id(arr):
    max = -1
    for i in arr:
        if max < i["id"]:
            max = i["id"]
    if max != -1: return max
    else: return {"error":"no content"}, 204

def get_colums_for_profile(data):
    stack,experience,description,can_solve,url_resume,portfolio,success_score = data["stack"],data["experience"],data["description"],data["can_solve"],data["url_resume"],data["portfolio"],data["success_score"]
    return stack,experience,description,can_solve,url_resume,portfolio,success_score

def find_lead_index(lead_id):
    for lead in leads:
        if lead["id"] == lead_id:
            return leads.index(lead)

def get_columns_for_leads(data):
    source_id,text,url,author,source,title,score,group=data["source_id"],data["text"],data["url"],data["author"],data["source"],data["title"],data["score"],data["group"]
    return source_id,text,url,author,source,title,score,group

@app.route('/')
def home():
    return {"status":"ok", "message":"ai project already set"}
#http://127.0.0.1:5000/

@app.route("/leads", methods=["GET"])
def get_leads():
    return leads
#http://127.0.0.1:5000/leads

@app.route('/leads', methods=["POST"])
def create_lead():
    data = request.get_json()
    source_id, text, url, author, source, title, score, group = get_columns_for_leads(data)
    leads.append({"id":leads[-1]["id"]+1, "source":source, "source_id":source_id, "title":title, "text":text, "url":url, "author":author, "score":score, "group":group})
    return {"message":"lead was inserted", "your lead":leads[-1]}
'''curl -X POST http://127.0.0.1:5000/leads \
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
    for lead in leads:
        if lead["id"] == lead_id:
            return lead
    abort(404)
#http://127.0.0.1:5000/leads/3

@app.route("/health")
def get_health():
    return {"ok": True}
#http://127.0.0.1:5000/health

@app.route('/leads/<int:lead_id>', methods=["PUT"])
def update_lead(lead_id):
    data = request.get_json()
    for lead in leads:
        if lead["id"] == lead_id:
            data["id"] = lead_id
            lead.update(data)
            return {"message": "lead was updated", "lead": lead}
    abort(404)

"""
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
    idx = find_lead_index(lead_id)
    if idx is not None: leads.pop(idx); return {"message":f'lead number {lead_id} was deleted'}
    else: abort(400)
#curl -X DELETE http://127.0.0.1:5000/leads/1

@app.route('/leads/search')
def search_leads():
    data = request.json()
    score = get_columns_for_leads(data)[-1]
    #ml reading i do for score but we need context too
    after_search = []
    for lead in leads:
        if lead["score"] >= score:
            after_search.append(lead)
    if len(after_search) > 0: return after_search
    else: abort(404)
#no

@app.route('/filter', methods=["GET"])
def filter_leads_by_param():
    param = request.args.get('context')
    if param == None: return {"error":"bad request< there is not context param in url"}, 400
    result = []
    for lead in leads:
        source_id,text,url,author,source,title,score,group = get_columns_for_leads(lead)
        params = [source_id,text,url,author,source,title,score,group]
        if param in params: result.append(lead)
    if len(result)!=0: return result
    else: abort(404)
#http://127.0.0.1:5000/filter?context=user123

@app.route('/profiles', methods=["GET"])
def get_profiles():
    return profiles
#http://127.0.0.1:5000/profiles

@app.route('/profile/<int:profile_id>', methods=["GET"])
def get_profile(profile_id):
    for profile in profiles:
        if profile["id"] == profile_id:
            return profile
    abort(404)
#http://127.0.0.1:5000/profile/1

@app.route('/profile', methods=["POST"])
def create_profile():
    data = request.get_json()
    stack,experience,description,can_solve,url_resume,portfolio,success_score = get_colums_for_profile(data)
    profiles.append({"id":find_max_id(profiles)+1, "stack":stack, "experience":experience, "description":description, "can_solve":can_solve, "url_resume":url_resume,"portfolio":portfolio, "success_score":success_score})
    return {"message":"new profile was inserted"}

if __name__ == "__main__":
    app.run(debug=True)