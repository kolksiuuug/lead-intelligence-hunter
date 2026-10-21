import os
import logging
from app.llm.predict import predict_issue
from app.llm.dataset import build_profile_dataset
from flask import request,jsonify
from app.main import app
from app.db import db
import json
from app.models import Lead,Profile,Finded
from app.services.llm_service import launch_model,lead_analyze_final,params
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)

def analyze_item(item):
    profiles = db.session.query(Profile).all()
    if not isinstance(item, dict): raise ValueError("ERROR LLM TYPE ANALYZING")
    issue_score,max_profile_id,max_profile_score = predict_issue(item["title"], item["description"], None, profiles)
    profile = db.session.get(Profile, max_profile_id)
    profile_data = build_profile_dataset(profile)
    if issue_score is None or max_profile_id is None or max_profile_score is None: raise NotImplementedError("NOT RESULT FOR LLM ANALYZE")
    match_explanation = launch_model(lead_analyze_final, f"{json.dumps(profile_data, ensure_ascii=False)}", params, False)
    if isinstance(match_explanation, dict):
        match_explanation = match_explanation.get("explanation",json.dumps(match_explanation, ensure_ascii=False))
    else:
        match_explanation = str(match_explanation)
    return issue_score,max_profile_id,max_profile_score,match_explanation

@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    items = data.get("items")
    if not isinstance(items, list): return jsonify({"error": "items должен быть списком"}), 400
    results = []
    for item in items:
        if not isinstance(item, dict): continue
        try:
            issue_score,max_profile_id,max_profile_score,match_explanation = analyze_item(item)
            lead_fields = {"source_id":item["provider"],"text":item["description"],"title":item["title"],"url":item["html_url"],"author":item["provider"],"source":item["provider"],"group_name":float(max_profile_score),"score":float(issue_score),"best_profile_id":max_profile_id,"match_explanation":str(match_explanation)}
            lead = Lead(**lead_fields)
            db.session.add(lead)
            finded = Finded(group=item["provider"], priznak=item["priznak"])
            db.session.add(finded)
            db.session.commit()
            results.append({
                "success": True,
                "lead_id": lead.id,
                "priznak": item["priznak"],
                "score": issue_score,
                "best_profile_id": max_profile_id,
                "match_score": max_profile_score,
                "match_explanation": match_explanation
            })
            logger.info(results[-1])

        except Exception as e:
            db.session.rollback()
            logger.exception("Ошибка сохранения лида")

            results.append({
                "success": False,
                "priznak": item.get("priznak"),
                "error": str(e)
            })
    return jsonify({
        "processed": len(results),
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)