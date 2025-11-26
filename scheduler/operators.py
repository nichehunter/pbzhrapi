from apscheduler.schedulers.background import BackgroundScheduler
from scheduler.tasks import *
import atexit
import time


def start():
    scheduler = BackgroundScheduler()

    # scheduler.add_job(GenerateMonthAllowance, 'interval', seconds=5, id='GenerateMonthAllowance', max_instances=1000)
    # scheduler.add_job(GenerateMonthDeduction, 'interval', seconds=5, id='GenerateMonthDeduction', max_instances=1000)
    scheduler.add_job(GenerateMonthOrganizationContribution, 'interval', seconds=5, id='GenerateMonthOrganizationContribution', max_instances=1000)

    # scheduler.add_job(
    #     CertificateExpire,
    #     trigger='cron',
    #     hour=0,
    #     minute=5,
    #     id='CertificateExpire',
    #     max_instances=1,  # ensure only one instance at a time
    #     replace_existing=True
    # )


    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())
