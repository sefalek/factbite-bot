"""Delete generated post folders older than RETENTION_DAYS.
Never touches data/topic_history.json or source files.
V3 dry-run uses this script only when explicitly requested.
"""
import datetime, os, shutil

RETENTION_DAYS = int(os.environ.get("FACTBITE_RETENTION_DAYS", "14"))
ROOT = "posts"
cutoff = datetime.datetime.now() - datetime.timedelta(days=RETENTION_DAYS)
removed = 0
if os.path.isdir(ROOT):
    for name in os.listdir(ROOT):
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path):
            continue
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            continue
        if mtime < cutoff:
            shutil.rmtree(path)
            removed += 1
            print("Removed:", path)
print(f"V3 cleanup complete: {removed} folders older than {RETENTION_DAYS} days removed.")
