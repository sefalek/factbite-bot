"""Delete generated post folders older than retention period."""
import datetime, os, shutil
RETENTION_DAYS=int(os.environ.get("FACTBITE_RETENTION_DAYS","14")); ROOT="posts"
cutoff=datetime.datetime.now()-datetime.timedelta(days=RETENTION_DAYS)
if os.path.isdir(ROOT):
    for name in os.listdir(ROOT):
        path=os.path.join(ROOT,name)
        if os.path.isdir(path) and datetime.datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
            shutil.rmtree(path); print("Removed:",path)
print("FactBite cleanup complete")
