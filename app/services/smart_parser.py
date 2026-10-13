def note_to_dict(note):
    return {"id":note.id, "text":note.text, "purpose":note.purpose, "profile_id":note.profile_id, "leads":[lead.id for lead in note.leads]}
def lead_to_dict(lead):
    return {"id":lead.id, "source":lead.source, "source_id":lead.source_id, "title":lead.title, "text":lead.text, "url":lead.url, "author":lead.author, "score":lead.score, "group":lead.group_name}
def profile_to_dict(profile):
    return {"id":profile.id, "stack":profile.stack, "experience":profile.experience, "description":profile.description, "can_solve":profile.can_solve, "url_resume":profile.url_resume, "portfolio":profile.portfolio, "success_score":profile.success_score}


def get_colums_for_profile(data):
    stack,experience,description,can_solve,url_resume,portfolio,success_score = data["stack"],data["experience"],data["description"],data["can_solve"],data["url_resume"],data["portfolio"],data["success_score"]
    return stack,experience,description,can_solve,url_resume,portfolio,success_score

def get_columns_for_leads(data):
    source_id,text,url,author,source,title,score,group=data["source_id"],data["text"],data["url"],data["author"],data["source"],data["title"],data["score"],data["group"]
    return source_id,text,url,author,source,title,score,group
