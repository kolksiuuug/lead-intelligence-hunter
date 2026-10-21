from dotenv import load_dotenv
import time
load_dotenv()
import requests
from random import randint
import os, logging, json
from app.models import Finded
from app.db import db
import uuid
from html import unescape
from app.main import app
from datetime import datetime
random_flag = os.getenv("RANDOM_FLAG", "false")
kword_size = int(os.getenv("COLLECTOR_SIZE_KWORK", "5"))
kword_size = max(kword_size, 2)
proxy = os.getenv("PROXY_COLLECTORS", None)
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)
import re
headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
    }
import random

def generate_headers():
    user_agents = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    ]

    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
    }
headers_workspace = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
    }
headers_youdo = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
        "Content-Type":"application/json",
    }

def generate_random_pages(flag):
    if flag == "true": return [str(randint(1, kword_size*100)) for _ in range(kword_size)]
    return [str(i+1) for i in range(kword_size+1)]


def flRU():
    logger.info("COLLECTOR FLRU WAS INITIALIZED")
    url_template = "https://www.fl.ru"
    url_main = ["https://www.fl.ru/projects/?kind=1", "https://www.fl.ru/projects/page-2/?kind=1", "https://www.fl.ru/projects/page-3/?kind=1"]
    url_new = []
    for url in url_main:
        try:
            request = requests.get(url, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy})
            request.raise_for_status()
        except Exception as e:
            logger.warning("Ошибка запроса FLRU страницы %s", e)
            continue

        result = request.text
        links = re.findall(r'"(/projects/\d+/[^"]+\.html)"', result)
        for link in links: url_new.append(url_template+link)
    url_new = list(dict.fromkeys(url_new))
    function_result = []
    for url in url_new:
        try: 
            request = requests.get(url, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy})
            request.raise_for_status()
        except Exception as e:
            logger.warning("Ошибка запроса FLRU страницы %s", e)
            continue
        match_priznak = re.search(r'Опубликован\s+(\d{2}\.\d{2}\.\d{4})\s+в\s+(\d{2}:\d{2})', request.text)
        if not match_priznak: continue
        date = datetime.strptime(match_priznak.group(1) + " " + match_priznak.group(2), "%d.%m.%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        priznak = match_priznak.group(1)+"/"+match_priznak.group(2)
        flag = db.session.query(Finded).filter_by(priznak=priznak).first()            
        if flag or "Заказчик выбрал исполнителя" in request.text: continue
        match = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', request.text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            name = data.get("name")
            description = data.get("description")
            html_url = url
            function_result.append({"priznak":priznak, "html_url":html_url,"title":name, "description":description, "date":date, "date_expire":None, "provider":"flRU"})
    return function_result

def kwork():
    logger.info("COLLECTOR KWORK WAS INITIALIZED")
    url_template="https://kwork.ru/projects"
    pages = generate_random_pages(random_flag)
    final_list_ouput = []
    for page in pages:
        try:
            request = requests.post(url_template, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy}, params={"utm_source":"chatgpt.com", "page":page})
            request.raise_for_status()
        except Exception as e:
            logger.warning("Ошибка запроса KWORK страницы %s: %s", page, e)
            continue
        result = request.json()
        projects = result.get("data", {}).get("pagination", {}).get("data", [])
        for project in projects:
            ids = str(project["id"])
            flag = db.session.query(Finded).filter_by(priznak=ids).first()
            if not flag and project["status"] == "active":
                final_list_ouput.append({"priznak":ids, "title":project["name"], "description":project["description"], "html_url":f"https://kwork.ru/projects/{ids}/view", "date_expire":project["date_expire"], "date":project["date_create"],"provider":"kwork"})
    return final_list_ouput
months = {
    "января": "01", "февраля": "02", "марта": "03",
    "апреля": "04", "мая": "05", "июня": "06",
    "июля": "07", "августа": "08", "сентября": "09",
    "октября": "10", "ноября": "11", "декабря": "12"
}
def workspace():
    logger.info("COLLECTOR WORKSPACE WAS INITIALIZED")
    global months
    final_list = []
    url_template = "https://workspace.ru"
    url_projects = "https://workspace.ru/tenders/"
    pages = generate_random_pages(random_flag)
    new_links = []
    for page in pages:
        try:
            request = requests.get(url_projects, headers=headers_workspace, timeout=15, proxies={"http": proxy, "https": proxy}, params={"STATUS":"published", "SORT":"public","ORDER":0, "page":int(page)})
            request.raise_for_status()
        except Exception as e:
            logger.warning("Ошибка запроса WORKSPACE страницы %s: %s", page, e)
            continue
        result = request.json()
        tender_html = result.get("tender", "")
        links = re.findall(r'href=["\'](/tenders/[^"\']+)["\']', tender_html)
        for link in links:
            match = re.search(r'/tenders/[^/]+-(\d+)/?', link)
            if not match: continue
            priznak = match.group(1)+"__WORKSPACE"
            prz = db.session.query(Finded).filter_by(priznak=priznak).first()
            if not prz: new_links.append({"priznak":priznak,"html_url":url_template+link})
    new_links = list({item["priznak"]: item for item in new_links}.values())
    for link in new_links:
        priznak = link["priznak"]
        url = link["html_url"]
        request = requests.get(url, headers=headers, timeout=15, proxies={"http": proxy, "https": proxy})
        result = request.text
        match_title = re.search(r'<h1 class="tendercard__title">\s*(.*?)\s*<div', result, re.DOTALL)
        title = unescape(match_title.group(1)).strip() if match_title else None
        match_description=re.search(r'<div class="tendercard__desc[^"]*">(.*?)</div>', result, re.DOTALL)
        description = (unescape(re.sub(r'<[^>]+>', ' ', match_description.group(1))) if match_description else None)
        if description: description = re.sub(r'\s+', ' ', description).strip()
        match_date = re.search(r'<div class="b-tender__info-item-title">\s*Опубликован:\s*</div>\s*'r'<div class="b-tender__info-item-text">\s*(.*?)\s*</div>',result, re.DOTALL)
        date = unescape(match_date.group(1)).strip() if match_date else None
        if date: day,month,year=date.split();date=datetime.strptime(f"{day}.{months[month]}.{year}", "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
        match_date_expire = re.search(r'<div class="b-tender__info-item-title">\s*Крайний срок приема заявок:\s*</div>\s*'r'<div class="b-tender__info-item-text">\s*(.*?)\s*</div>',result,re.DOTALL)
        date_expire = unescape(match_date_expire.group(1)).strip() if match_date_expire else None
        if date_expire: day,month,year=date_expire.split();date_expire=datetime.strptime(f"{day}.{months[month]}.{year}", "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
        final_list.append({"priznak":priznak, "title":title, "description":description, "html_url":url, "date_expire":date_expire, "date":date,"provider":"workspace"})
    return final_list

def youdo():
    session = requests.Session()
    session.headers.update(headers_youdo)
    logger.info("COLLECTOR YOUDO WAS INITIALIZED")
    url_template = "https://youdo.com"
    url_task = "https://youdo.com/api/tasks/task/"
    url_tasks = "https://youdo.com/api/tasks/tasks/"
    pages = generate_random_pages(random_flag)
    url_new = []
    final_list = []
    for page in pages:
        try:
            request = session.post(url_tasks, timeout=15, proxies={"http": proxy, "https": proxy}, json={"q":"","list":"all","status":"opened","radius":50,"lat":55.755864,"lng":37.617698,"page":page,"noOffers":False,"onlySbr":False,"onlyB2B":False,"onlyVacancies":False,"priceMin":"","sortType":1,"onlyVirtual":False,"categories":["all"],"searchRequestId":str(uuid.uuid4())})
            request.raise_for_status()
        except Exception as e:
            logger.warning("Ошибка запроса YOUDO страницы %s: %s", page, e)
            time.sleep(2)
            continue
        result = request.json()["ResultObject"]["Items"]
        for res in result:
            url_new.append({"id":res["Id"], "html_url":url_template+res["Url"], "status":res["StatusFlag"]})
    final = []
    session.headers.update(generate_headers())
    for url in url_new:
        priznak = str(url["id"])+"__YOUDO"
        if url["status"] == "new":
            flag = db.session.query(Finded).filter_by(priznak=priznak).first()
            if flag: continue
            html_url = url["html_url"]
            try:
                request1 = session.get(url_task+str(url["id"]), timeout=15, proxies={"http": proxy, "https": proxy})
                request1.raise_for_status()
            except Exception as e:
                logger.warning("Ошибка запроса YOUDO страницы %s: %s", url["html_url"], e)
                time.sleep(2)
                continue
            result = request1.json()["ResultObject"]["TaskData"]
            if result["Dates"]["CreationDate"]:
                date = datetime.fromtimestamp(result["Dates"]["CreationDate"]/1000)
                date = date.strftime("%Y-%m-%d %H:%M:%S")
            else: date = None
            if result["Dates"]["NeedEndDate"]:
                date_expire = datetime.fromtimestamp(result["Dates"]["NeedEndDate"]/1000)
                date_expire = date_expire.strftime("%Y-%m-%d %H:%M:%S")
            else: date_expire = None
            final.append({"priznak":priznak, "title":result["Title"], "description":result["Description"], "html_url":html_url, "date_expire":date_expire, "date":date,"provider":"youdo"})
    return final



def collectors():
    start_time = time.time()
    future1 = flRU()
    future2 = workspace()
    future3 = youdo()
    future4 = kwork()
    final_data=[*future1,*future2,*future3,*future4]
    logger.info(f"Сбор завершен за {time.time() - start_time:.2f} сек. Всего элементов: {len(final_data)}")
    return  final_data

def get_new_data(final_data):
    if not final_data: return []
    signs={item["priznak"] for item in final_data if item.get("priznak")}
    if not signs: return []
    existing_rows=(db.session.query(Finded.priznak).filter(Finded.priznak.in_(signs))).all()
    existing_signs = {row[0] for row in existing_rows}
    seen=set()
    new_items=[]
    for item in final_data:
        sign=item.get("priznak")
        if not sign or sign in existing_signs or sign in seen: continue
        new_items.append(item)
        seen.add(sign)
    return new_items



def main():
    with app.app_context():
        final_data = collectors()
        new_items = get_new_data(final_data)

        logger.info(
            "Собрано: %d, новых заданий: %d",
            len(final_data),
            len(new_items)
        )

        if not new_items:
            logger.info("Новых заданий для анализа нет")
            return

        try:
            response = requests.post(
                "http://llm:8000/analyze",
                json={"items": new_items},
                timeout=180
            )
            response.raise_for_status()
            logger.info("Ответ LLM: %s", response.json())

        except requests.RequestException:
            logger.exception("Не удалось передать задания в LLM")

flag = os.getenv("RUNNER_COLLECTORS", "false")
internal = int(os.getenv("RUNNER_COLLECTORS_INTERVAL", "10"))*60
if __name__ == "__main__" and flag=="true":
    while True:
        try:
            main()
        except Exception as e: logger.info(f"{e} on collectors")
        time.sleep(internal)

