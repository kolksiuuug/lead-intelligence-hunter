import joblib,logging
from pathlib import Path
from dotenv import load_dotenv
from app.services.llm_service import launch_model,profile_matcher_format,profile_matcherchik_new
from app.llm.dataset import build_text_issue
MODEL_PATH = Path(__file__).resolve().parents[2] / "issue_score_model.joblib"
PMODEL_PATH = Path(__file__).resolve().parents[2] / "issue_matcher_model.joblib"
import os,json
load_dotenv()
model = (joblib.load(MODEL_PATH) if os.path.isfile(MODEL_PATH) else None)
model_profile = (joblib.load(PMODEL_PATH) if os.path.isfile(PMODEL_PATH) else None)
logging.basicConfig(level=logging.INFO,format="%(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)
not_self_llm_analyze = os.getenv("LLM_SELF_PROFILE_ANALITIC", "false")
def predict_issue(title, body=None, comments=None, profiles=None):
    issue = {"title": title,"body": body,"comments": comments or []}
    text = build_text_issue(issue)
    score = float(model.predict([text["task"]])[0])
    score = max(0.0, min(1.0, score))
    result_score_profiles = []
    for profile in profiles or []:
        text_profile = build_text_issue(issue, profile)
        score_profile = float(model_profile.predict([text_profile["task_new"]])[0])
        score_profile = max(0.0, min(1.0, score_profile))
        profile_id = (profile.get("id") if isinstance(profile, dict) else profile.id)
        if score_profile<0.6: logger.info(f"LLM SCORED PROFILE ID {profile_id} like {score_profile}")
        prompt = f"""
        TASK:
        {json.dumps(issue, ensure_ascii=False, default=str)}

        TASK_AND_PROFILE:
        {text_profile['task_new']}

        Evaluate how well this profile matches the task. Consider domain compatibility, essential skills, relevant experience, and missing qualifications. Do not invent skills or award high scores based on keyword overlap alone.

        Return the profile ID and match score as JSON.
        """
        if not_self_llm_analyze=="true":
            logger.warning("SELF LLM IS NOT ACTIVE FOR PROFILE ANALYZE")
            result = launch_model(profile_matcherchik_new, prompt, profile_matcher_format, False)
            profile_id = result["id"]
            score_profile = result["score"]
        result_score_profiles.append({"id": profile_id,"score": score_profile})
    if result_score_profiles:
        best_profile = max(result_score_profiles,key=lambda x: x["score"])
        max_profile_id = best_profile["id"]
        max_profile_score = round(best_profile["score"], 4)
    else:
        max_profile_id = None
        max_profile_score = None
    return round(score, 4), max_profile_id, max_profile_score

