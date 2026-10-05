from flask import Flask
from flask import request
app = Flask(__name__)

leads = [{
  "id": 1,
  "source": "reddit",
  "source_id": "abc123",
  "title": "Someone is looking for a security tool",
  "text": "I need a tool that...",
  "url": "https://example.com/post/123",
  "author": "user123",
  "score": 0.87
  },
  {
  "id": 2,
  "source": "fff",
  "source_id": "sss",
  "title": "security new",
  "text": "I need a lang that...",
  "url": "https://example.com/post/433",
  "author": "user33323",
  "score": 0.27
  }
]

def get_columns_for_leads(data):
    source_id,text,url,author,source,title,score=data["source_id"],data["text"],data["url"],data["author"],data["source"],data["title"],data["score"]
    return source_id,text,url,author,source,title,score

@app.route('/')
def home():
    return {"status":"ok", "message":"ai project already set"}

@app.route("/leads", methods=["GET"])
def get_leads():
    return leads

@app.route('/leads', methods=["POST"])
def create_lead():
    data = request.get_json()
    source_id, text, url, author, source, title, score = get_columns_for_leads(data)
    leads.append({"id":len(leads)+1, "source":source, "source_id":source_id, "title":title, "text":text, "url":url, "author":author, "score":score})
    return {"message":"lead was inserted", "your lead":leads[-1]}

@app.route('/leads/<int:lead_id>')
def get_lead(lead_id):
    for lead in leads:
        if lead["id"] == lead_id:
            return lead
    return {"error":"no same leads"}

@app.route("/health")
def get_health():
    return {"ok"}

@app.route('/leads/<int:lead_id>', methods=["PUT"])
def update_lead(lead_id):
    data = request.get_json()
    source_id, text, url, author, source, title, score = get_columns_for_leads(data)
    for lead in leads:
        if lead["id"] == lead_id:
            lead[lead_id] = {"id":lead_id, "source":source, "source_id":source_id, "title":title, "text":text, "url":url, "author":author, "score":score}
            return {"message":"lead was updated"}
    return "no leads were updated"

@app.route('/leads/<int:lead_id>', methods=["DELETE"])
def delete_lead(lead_id):
    leads.pop(lead_id-1)
    return {"message":f'lead number {lead_id} was deleted'}

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
    else: return {"message":"no leads for your opportunities"}

if __name__ == "__main__":
    app.run(debug=True)