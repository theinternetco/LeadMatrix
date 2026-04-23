from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import time

def my_job(message):
    print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] JOB FIRED! → {message}\n")

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.start()

run_at = datetime.now() + timedelta(seconds=30)
scheduler.add_job(
    my_job,
    trigger = DateTrigger(run_date=run_at),
    args    = ["APScheduler is working!"],
    id      = "test_job"
)

print(f"⏰ Scheduled for : {run_at.strftime('%H:%M:%S')}")
print(f"   Current time  : {datetime.now().strftime('%H:%M:%S')}")
print(f"   Waiting 35 seconds...\n")

for i in range(35):
    time.sleep(1)
    if i % 10 == 0 and i > 0:
        print(f"   ... {i}s elapsed")

scheduler.shutdown()
print("Done.")