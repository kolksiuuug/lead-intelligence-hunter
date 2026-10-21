from app.models import IssueAnalysis,ProfileMatching
from app.db import db

def save_issue_analysis(issue, analysis, model_version):
    existing = IssueAnalysis.query.filter_by(issue_id=issue.id).first()
    if existing is None:
        existing = IssueAnalysis(issue_id=issue.id)
        db.session.add(existing)
    existing.score = analysis["score"]
    existing.label = analysis["label"]
    existing.reason = analysis["reason"]
    existing.model_version = model_version
    existing2 = ProfileMatching.query.filter_by(issue_id=issue.id).first()
    if existing2 is None:
        existing2 = ProfileMatching(issue_id=issue.id)
        db.session.add(existing2)
    existing2.best_profile_id = analysis["best_profile_id"]
    existing2.match_score = analysis["match_score"]
    existing2.match_explanation = analysis["match_explanation"]
    try: db.session.commit()
    except Exception as e: 
        db.session.rollback()
        raise KeyError("Database was not commited")
    print(f"\nISSUE_PARAMETERS:\nid:{existing.issue_id}\nscore:{existing.score}\nlabel:{existing.label}\nmodel_version:{model_version}\nreason:{existing.reason}\nbest_profile_id:{existing2.best_profile_id}\nmatch_score:{existing2.match_score}\nmatch_explanation:{existing2.match_explanation}\nEND\n")
