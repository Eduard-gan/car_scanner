from providers.polovni_automobili import PolovniAutomobili
from logic import fetch_and_save_to_db
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


scheduler = BlockingScheduler()
scheduler.add_job(
    func=fetch_and_save_to_db,
    kwargs={'provider': PolovniAutomobili(brand='volvo', model='xc90')},
    trigger=CronTrigger(minute='*/1', hour='*', day='*', month='*', timezone='Europe/Belgrade')
)
scheduler.start()
