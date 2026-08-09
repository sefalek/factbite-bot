import json,os
from datetime import datetime
from zoneinfo import ZoneInfo
p=json.load(open('data/daily_plan.json',encoding='utf-8')); now=datetime.now(ZoneInfo('Europe/Istanbul')); time=now.strftime('%H:%M'); special=p.get('special') or []; is_special=(time=='13:30' and bool(special))
if is_special: cat='culture'; fmt='classic'; name=special[0].get('name','Özel Gün')
else:
 slots=p.get('slots',[]); slot=next((x for x in slots if x.get('time')==time),slots[0] if slots else {}); cat=slot.get('category','general'); fmt=slot.get('format','classic'); name=''
out=os.environ.get('GITHUB_OUTPUT')
if out:
 with open(out,'a',encoding='utf-8') as f:f.write(f'category={cat}\nformat={fmt}\nspecial={name}\nis_special={str(is_special).lower()}\n')
print(cat,fmt,name,is_special)
