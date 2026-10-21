from app.services.llm_service import generate_search_terms
import requests
import os
import logging
from app.services.issue_analysis_service import save_issue_analysis
import time
from app.services.llm_service import analyze_github_issue
from dotenv import load_dotenv
from app.db import db
from app.models import Repositories,Issue,Comment,IssueAnalysis,ProfileMatching,Profile
from datetime import datetime,timezone
load_dotenv()
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)
max_github_requests=int(os.getenv("MAX_GITHUB_REQUESTS_PER_RUN", "500"))
max_repo_per_word=int(os.getenv("MAX_REPOSITORIES_PER_WORD", "3"))
max_issues_per_word=int(os.getenv("MAX_ISSUES_PER_WORD", "100"))
max_comments_per_word=int(os.getenv("MAX_COMMENTS_PER_WORD", "100"))
proxy = os.getenv("PROXY_GITHUB") or None
headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
#data = generate_search_terms() -  openrouter list 20 words

github_requests_count = 0

def github_get(url, **kwargs):
    global github_requests_count
    if max_github_requests <= github_requests_count:
        raise RuntimeError("Github Limits Reached")
    github_requests_count+=1
    response=requests.get(url, **kwargs)
    response.raise_for_status()
    return response

def url_request_github(query):
    global max_repo_per_word
    final=[]
    url = "https://api.github.com/search/repositories"
    try:
        response = github_get(url, params={"q":query,"per_page": max_repo_per_word}, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy})
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ERROR: {e}")
        return []
    data = response.json()["items"]
    logger.info(f"Repository:{response.status_code}\n")
    for item in data:
        final.append({"id":item["id"],"full_name":item["full_name"], "html_url":item["html_url"], "language":item["language"], "stargazers_count":item["stargazers_count"], "pushed_at":item["pushed_at"]})
        #print(f"repository[{item["html_url"]}] : {response.status_code}\n")
    return final

def save_repositories(repositories):
    saved = 0
    for repo in repositories:
        if Repositories.query.filter_by(github_id=repo["id"]).first() is None:
            saved+=1
            repo_db = Repositories(github_id=repo["id"],full_name=repo["full_name"],last_scanned_at=datetime.now(timezone.utc))
            db.session.add(repo_db)
    db.session.commit()
    return saved

def url_request_github_issues(full_name):
    global max_issues_per_word
    full_name = full_name.split('/')
    owner,repo=full_name[0],full_name[1]
    try:
        response = github_get(f"https://api.github.com/repos/{owner}/{repo}/issues",params={"per_page": max_issues_per_word, "state": "all"}, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
            print(f"HTTP ERROR: {e}")
            return []
    issues = response.json()
    clean_issues = []
    logger.info(f"Issue:{response.status_code}\n")
    for issue in issues:
            if ("pull_request" not in issue.keys()) and (issue.get("title", "").strip()) and (issue["body"] is not None and issue.get("body", "").strip()) and (issue["title"].strip().lower() != "spam"):
                clean_issues.append({"id":issue["id"],"title":issue["title"].strip(),"body":issue["body"],"html_url":issue["html_url"],"number":issue["number"],"labels":issue["labels"]})
                #print(f"issue[{issue["html_url"]}] : {response.status_code}\n")
    return clean_issues
##################
def save_issues(issues, repository_id):
    saved = 0
    for issue in issues:
        if Issue.query.filter_by(github_id=issue["id"]).first() is None:
            saved+=1
            issue_db = Issue(github_id=issue["id"],repository_id=repository_id,title=issue["title"],body=issue["body"],html_url=issue["html_url"],number=issue["number"])
            db.session.add(issue_db)
    db.session.commit()
    return saved

def url_request_github_comments(full_name, issue_number):
    global max_comments_per_word
    full_name=full_name.split('/')
    owner,repo=full_name[0],full_name[1]
    try:
        response = github_get(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments", params={"per_page":max_comments_per_word, "state":"all"}, headers=headers, timeout=15, proxies={"http":proxy, "https":proxy})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP ERROR: {e}")
        return []
    comments = response.json()
    result=[]
    logger.info(f"Comment:{response.status_code}\n")
    for comment in comments:
        if comment["body"] is not None and comment.get("body", "").strip():
            result.append({"github_id":comment["id"],"body":comment["body"],"html_url":comment["html_url"]})
            #print(f"comment[{comment["html_url"]}] : {response.status_code}\n")
    return result

def save_comments(comments, issue_id):
    saved = 0
    for comment in comments:
        if Comment.query.filter_by(github_id=comment["github_id"]).first() is None:
            saved+=1
            comment_db = Comment(github_id=comment["github_id"],issue_id=issue_id,body=comment["body"])
            db.session.add(comment_db)
    db.session.commit()
    return saved

flag = os.getenv("OLLAMA", None)
def analysis_unlabled_issues(repository_id):
    print("\n\n----------Analyzing pipeline is starting----------\n")
    analyzed = 0
    issues = Issue.query.filter_by(repository_id=repository_id).all()
    for issue in issues:
        existing = IssueAnalysis.query.filter_by(issue_id=issue.id).first()
        existing_matching = ProfileMatching.query.filter_by(issue_id=issue.id).first()
        if existing and existing_matching: continue
        try:
            profiles = Profile.query.all()
            analysis = analyze_github_issue(issue, profiles)
            model = analysis["model_version"]
            save_issue_analysis(issue, analysis, model)
            analyzed+=1
        except Exception as e: 
            db.session.rollback()
            logger.error(f"error with issue analize: {e}")
        if not flag:
            time.sleep(2)
    logger.info("\n----------Analyzing pipeline was ended----------\n")
    return analyzed

def analyze_repository(word):
    analyzed = 0
    issues_saved = 0
    comments_saved = 0
    repositories=url_request_github(word)
    repo_saved = save_repositories(repositories)
    for repo in repositories:
        repo_db = Repositories.query.filter_by(github_id=repo["id"]).first()
        issues = url_request_github_issues(repo["full_name"])

        existing_issues={row[0] for row in db.session.query(Issue.github_id).filter_by(repository_id=repo_db.id).all()}
        issues_saved += save_issues(issues, repo_db.id)

        for issue in issues:
            if issue["id"] in existing_issues: continue
            comments = url_request_github_comments(repo["full_name"], issue["number"])

            issue_db=Issue.query.filter_by(github_id=issue["id"], repository_id=repo_db.id).first()
            if issue_db: 
                comments_saved+=save_comments(comments, issue_db.id)

        repo_db.last_scanned_at=datetime.now(timezone.utc)
        db.session.commit()
        analyzed += analysis_unlabled_issues(repo_db.id)
    print(f"\n\n!------SUMMARY------!\nrepositories: {repo_saved}\nissues: {issues_saved}\ncomments: {comments_saved}\nissues_analyzed: {analyzed}\n!------GitHub_PipeLine WAS ENDED------!\n\n")


def run_discovery():
    global github_requests_count
    github_requests_count = 0
    from app.main import app
    with app.app_context():
        logger.info("\nGITHUB DISCOVERY STARTING\n")
        terms = generate_search_terms()
        if not isinstance(terms, list):
            raise ValueError("OPENROUTER must return an array")
        terms=[term.strip() for term in terms if isinstance(term, str) and term.strip()]
        terms=list(dict.fromkeys(terms))
        max_words=int(os.getenv("DISCOVERY_WORDS_PER_RUN", "5"))
        terms = terms[:max_words]
        logger.info(f"{terms} - this terms were generated")
        if not terms:
            raise ValueError("no valid terms")
        for index,term in enumerate(terms, start=1):
            print(f"\n{index}/{len(terms)} is enumerating\n")
            try:
                analyze_repository(term)
            except RuntimeError as e:
                db.session.rollback()
                if str(e)=="Github Limits Reached": break
                logger.exception("runtime error on this term:  \n", term)
            except Exception as exp:
                db.session.rollback()
                print(f"Failed for '{term}': \n{type(exp).__name__}: {exp}")

if __name__=="__main__":
    run_discovery()


