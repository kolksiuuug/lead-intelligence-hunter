from sqlalchemy import select
from app.db import db
from app.models import Lead
from app.services.normalize import normalize_url
from app.services.smart_parser import get_columns_for_leads


def save_lead(data):
    source_id1, text1, url1, author1, source1, title1, score1, group1 = get_columns_for_leads(data)

    lead = db.session.scalar(
        select(Lead).where(
            Lead.source == source1,
            Lead.source_id == source_id1
        )
    )

    if not source1 or not source_id1 or not url1:
        raise ValueError("source, source_id and url are required")

    url1 = normalize_url(url1)

    if lead is None:
        lead = Lead(
            source_id=source_id1,
            text=text1,
            url=url1,
            author=author1,
            source=source1,
            title=title1,
            score=score1,
            group_name=group1
        )
        db.session.add(lead)
        db.session.commit()
        return lead, {"message": "lead was created"}

    lead.url = url1
    lead.author = author1
    lead.text = text1
    lead.group_name = group1
    lead.score = score1
    lead.title = title1

    db.session.commit()
    return lead, {"message": "lead was updated"}