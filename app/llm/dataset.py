from sklearn.model_selection import train_test_split
from app.models import IssueAnalysis,Issue,TrainingSample,Profile,ProfileMatching
from app.db import db
import json

def build_profile_dataset(profile):
    if isinstance(profile, dict):
        return {"id": profile.get("id"),"stack": profile.get("stack"),"experience": profile.get("experience"),"description": profile.get("description"),"can_solve": profile.get("can_solve"),"url_resume": profile.get("url_resume"),"portfolio": profile.get("portfolio"),"success_score": profile.get("success_score")}
    return {"id": profile.id,"stack": profile.stack,"experience": profile.experience,"description": profile.description,"can_solve": profile.can_solve,"url_resume": profile.url_resume,"portfolio": profile.portfolio,"success_score": profile.success_score}


def build_text_issue(issue, profile=None):
    if isinstance(issue, dict):
        title = issue.get("title") or ""
        description = issue.get("description") or ""
        comments = issue.get("comments") or []
        github_id = issue.get("github_id", issue.get("id")) or None
    else:
        title = issue.title or ""
        description = issue.body or ""
        comments = [c.body for c in issue.comments if c.body]
        github_id = issue.github_id
    comments_text = "\n".join(c if isinstance(c, str) else (c.get("body") or "") for c in comments)
    task = f"{title}\n{description}\n{comments_text}"
    task_new = None

    if profile is not None:
        profile_data = build_profile_dataset(profile)
        profiles_text = json.dumps(profile_data,ensure_ascii=False)
        task_new = f"{task}\n{profiles_text}"

    return {"id": github_id,"task": task,"task_new": task_new}

def get_dataset():
    issues = db.session.query(IssueAnalysis).all()
    result = []
    result_profile=[]
    for issue in issues:
        nep = issue.issue
        if not nep: continue
        issue_builded = build_text_issue(issue.issue)
        result.append([issue_builded, float(issue.score)])
        profile_score_issue = db.session.query(ProfileMatching).filter_by(issue_id=issue.issue_id).first()
        if profile_score_issue is None or profile_score_issue.best_profile_id is None: continue
        best_profile = db.session.get(Profile, profile_score_issue.best_profile_id)
        if not best_profile: continue
        issue_builded_profile = build_text_issue(issue.issue, best_profile)
        result_profile.append([{"id":issue_builded_profile["id"], "task_new":issue_builded_profile["task_new"]}, float(profile_score_issue.match_score)])
    if len(result) < 2 or len(result_profile) < 2: raise ValueError("no data for training LLM")
    texts = [x[0]["task"] for x in result]
    scores = [float(x[1]) for x in result]
    ids = [x[0]["id"] for x in result]
    train_x,test_x,train_y,test_y,train_ids,test_ids=train_test_split(texts,scores,ids,test_size=0.3,random_state=42)
    texts_profile = [x[0]["task_new"] for x in result_profile]
    scores_profile = [float(x[1]) for x in result_profile]
    ids_profile = [x[0]["id"] for x in result_profile]
    train_x_profile,test_x_profile,train_y_profile,test_y_profile,train_ids_profile,test_ids_profile=train_test_split(texts_profile,scores_profile,ids_profile,test_size=0.3,random_state=42)
    return train_x,train_y,test_x,test_y,train_x_profile,test_x_profile,train_y_profile,test_y_profile
