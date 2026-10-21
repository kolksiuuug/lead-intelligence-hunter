import os
import time
import logging
from app.main import app
from app.services.repository_discovery import run_discovery
from app.llm.train import train_model
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)
flag = 0
def main():
    global flag
    enabled_work_on_start=os.getenv("DISCOVERY_RUN_ON_START", "true").lower() == "true"
    enabled = os.getenv("DISCOVERY_RUN_WORK", "true").lower() == "true"
    interval = int(os.getenv("DISCOVERY_INTERVAL_MINUTES", "24"))*60
    if enabled_work_on_start and flag==0:
        print("%%%%%%%%%%%%_STARTING_%%%%%%%%%%%%")
        time.sleep(30)
        try:
            print("\n-----------STARTING_PIPELINE--------\n") 
            run_discovery()
            print("\n-----------END_PIPELINE--------\n")
            flag=-1
            #time.sleep(15)
            with app.app_context():
                train_model()
            time.sleep(interval)
        except Exception:
            flag=1
            logger.exception("Initial discovery failed")              
    
    if not enabled:
        logger.info("Github collector is disabled")
        return
    
    logger.info("Waiting 120 seconds before the first run...")
    time.sleep(120)

    while flag<=0:
        try:
            print("\n-----------STARTING_PIPELINE--------\n") 
            run_discovery()
            print("\n-----------END_PIPELINE--------\n")
            with app.app_context():
                train_model()
            time.sleep(15)
        except Exception:
            logger.exception("Discovery pipeline failed")
        time.sleep(interval)

if __name__=="__main__":
    main()
