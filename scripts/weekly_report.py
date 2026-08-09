import json,os,urllib.parse,urllib.request
from datetime import datetime,timedelta,timezone
TOKEN=os.environ.get('IG_ACCESS_TOKEN'); USER=os.environ.get('IG_USER_ID'); TG=os.environ.get('TELEGRAM_BOT_TOKEN'); CHAT=os.environ.get('TELEGRAM_CHAT_ID')
if not all([TOKEN,USER,TG,CHAT]):raise SystemExit('Analytics secrets not configured')
BASE='https://graph.instagram.com/v21.0'
def get(path,params):
 q=urllib.parse.urlencode({**params,'access_token':TOKEN})
 with urllib.request.urlopen(f'{BASE}/{path}?{q}',timeout=30) as r:return json.loads(r.read())
def tg(msg):
 data=urllib.parse.urlencode({'chat_id':CHAT,'text':msg}).encode(); urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{TG}/sendMessage',data=data),timeout=20).read()
since=datetime.now(timezone.utc)-timedelta(days=7); data=get(f'{USER}/media',{'fields':'id,caption,media_type,timestamp,like_count,comments_count,permalink','limit':50}); items=[x for x in data.get('data',[]) if x.get('timestamp','')>=since.isoformat()]; likes=sum(int(x.get('like_count',0) or 0) for x in items); comments=sum(int(x.get('comments_count',0) or 0) for x in items)
try:followers=get(USER,{'fields':'followers_count'}).get('followers_count','?')
except Exception:followers='?'
best=max(items,key=lambda x:int(x.get('like_count',0) or 0)+3*int(x.get('comments_count',0) or 0),default={}); msg=f'📊 FactBite haftalık rapor\n\nGönderi: {len(items)}\n❤️ Beğeni: {likes}\n💬 Yorum: {comments}\n👤 Takipçi: {followers}\n\n🏆 En iyi içerik: {(best.get("caption") or "(başlıksız)")[:120]}'; tg(msg); print(msg)
