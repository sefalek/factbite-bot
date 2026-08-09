from pathlib import Path
from datetime import datetime,timedelta
root=Path('posts'); cutoff=datetime.now()-timedelta(days=14); removed=0
if root.exists():
 for d in root.iterdir():
  if not d.is_dir():continue
  try:m=datetime.fromtimestamp(d.stat().st_mtime)
  except OSError:continue
  if m<cutoff:
   for p in sorted(d.rglob('*'),reverse=True):
    if p.is_file():p.unlink(missing_ok=True)
    elif p.is_dir():p.rmdir()
   d.rmdir();removed+=1
print(f'Cleanup removed {removed} old post directories')
