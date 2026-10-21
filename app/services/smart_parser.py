def note_to_dict(note):
    return {
        "id": note.id,
        "text": note.text,
        "purpose": note.purpose,
        "profile_id": note.profile_id,
        "leads": [lead.id for lead in note.leads]
    }


def lead_to_dict(lead):
    return {
        "id": lead.id,
        "source": lead.source,
        "source_id": lead.source_id,
        "title": lead.title,
        "text": lead.text,
        "url": lead.url,
        "author": lead.author,
        "score": lead.score,
        "group": lead.group_name
    }


def profile_to_dict(profile):
    return {
        "id": profile.id,
        "stack": profile.stack,
        "experience": profile.experience,
        "description": profile.description,
        "can_solve": profile.can_solve,
        "url_resume": profile.url_resume,
        "portfolio": profile.portfolio,
        "success_score": profile.success_score
    }


def get_colums_for_profile(data):
    return (
        data.get("stack"),
        data.get("experience"),
        data.get("description"),
        data.get("can_solve"),
        data.get("url_resume"),
        data.get("portfolio"),
        data.get("success_score", 0.0)
    )


def get_columns_for_leads(data):
    return (
        data.get("source_id"),
        data.get("text"),
        data.get("url"),
        data.get("author"),
        data.get("source"),
        data.get("title"),
        data.get("score"),
        data.get("group")
    )

from sqlalchemy import select
from app.db import db
from app.models import (
    Repositories,
    Issue,
    Comment,
    IssueAnalysis,
    TrainingSample,
    ProfileMatching,
    AppSetting,
    Finded
)


def comment_to_dict(comment):
    return {
        "id": comment.id,
        "github_id": comment.github_id,
        "issue_id": comment.issue_id,
        "body": comment.body,
        "score": comment.score
    }


def issue_analysis_to_dict(analysis):
    if analysis is None:
        return None

    return {
        "id": analysis.id,
        "issue_id": analysis.issue_id,
        "score": analysis.score,
        "label": analysis.label,
        "reason": analysis.reason,
        "model_version": analysis.model_version
    }


def training_sample_to_dict(sample):
    if sample is None:
        return None

    return {
        "id": sample.id,
        "issue_id": sample.issue_id,
        "score": sample.score,
        "text": sample.text,
        "label": sample.label,
        "reason": sample.reason
    }


def profile_matching_to_dict(matching):
    if matching is None:
        return None

    return {
        "id": matching.id,
        "issue_id": matching.issue_id,
        "best_profile_id": matching.best_profile_id,
        "match_score": matching.match_score,
        "match_explanation": matching.match_explanation
    }


def issue_to_dict(issue):
    analysis = db.session.scalar(
        select(IssueAnalysis).where(IssueAnalysis.issue_id == issue.id)
    )
    sample = db.session.scalar(
        select(TrainingSample).where(TrainingSample.issue_id == issue.id)
    )
    matching = db.session.scalar(
        select(ProfileMatching).where(ProfileMatching.issue_id == issue.id)
    )

    return {
        "id": issue.id,
        "github_id": issue.github_id,
        "repository_id": issue.repository_id,
        "title": issue.title,
        "body": issue.body,
        "number": issue.number,
        "html_url": issue.html_url,
        "analysis": issue_analysis_to_dict(analysis),
        "training_sample": training_sample_to_dict(sample),
        "profile_matching": profile_matching_to_dict(matching),
        "comments": [comment_to_dict(comment) for comment in issue.comments]
    }


def repository_to_dict(repository, include_issues=True):
    result = {
        "id": repository.id,
        "github_id": repository.github_id,
        "full_name": repository.full_name,
        "last_scanned_at": (
            repository.last_scanned_at.isoformat()
            if repository.last_scanned_at else None
        ),
        "issues_count": len(repository.issues)
    }

    if include_issues:
        result["issues"] = [
            issue_to_dict(issue) for issue in repository.issues
        ]

    return result


def app_setting_to_dict(setting):
    return {
        "key": setting.key,
        "value": setting.value
    }


def finded_to_dict(finded):
    return {
        "id": finded.id,
        "group": finded.group,
        "priznak": finded.priznak
    }