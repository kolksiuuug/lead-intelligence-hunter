import re
def normalize_url(url):
    url = url.replace(' ', '').rstrip("/")
    url = url.split("/", 3)
    url[0] = url[0].lower()
    url[2] = url[2].lower()
    if len(url)>3: url[3] = re.sub(r'/+', '/', '/' + url[3]).lstrip('/')
    url = '/'.join(url)
    return url


