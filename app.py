from flask import Flask,render_template,jsonify
import requests,random,time
from datetime import datetime,timezone,timedelta
app=Flask(__name__)
API="https://ta.wikipedia.org/w/api.php"; PAGE="விக்கிப்பீடியா:விக்கி மாரத்தான் 2026"
START=datetime(2026,9,27,0,30,tzinfo=timezone.utc); END=datetime(2026,9,28,0,30,tzinfo=timezone.utc); OFF=timedelta(hours=5,minutes=30)
UA="TamilWikiMarathonDashboard/2.0 (https://github.com/sivakosaran/tawikimarathon; User:Sivakosaran)"
TASKS=[("மேற்கோள் சேர்த்தல்","சான்றுகள் தேவைப்படும் அனைத்துக் கட்டுரைகள்"),("பகுப்பு சேர்த்தல்","பகுப்பில்லாதவை"),("விக்கியாக்கம்","விக்கிப்படுத்தப்பட வேண்டிய கட்டுரைகள்"),("குறுங்கட்டுரைகளை விரிவாக்குதல்","குறுங்கட்டுரைகள்")]
S=requests.Session();S.headers.update({"User-Agent":UA,"Accept-Encoding":"gzip"});cache={}
def api(p):
 r=S.get(API,params={**p,"format":"json","formatversion":2},timeout=20);r.raise_for_status();d=r.json()
 if "error" in d:raise RuntimeError(d["error"].get("info","MediaWiki API error"))
 return d
def participants():
 ss=api({"action":"parse","page":PAGE,"prop":"sections"})["parse"]["sections"]
 idx=next((s["index"] for s in ss if "பங்களிக்க விரும்புபவர்கள்" in s.get("line","")),None)
 if idx is None:return []
 ls=api({"action":"parse","page":PAGE,"section":idx,"prop":"links"})["parse"].get("links",[])
 return sorted(set(x["title"].split(":",1)[1] for x in ls if x.get("ns")==2 and ":" in x.get("title","")),key=str.casefold)
def state(now):
 return "before" if now<START else ("finished" if now>=END else "live")
def contributions(users,end):
 rows=[]
 for i in range(0,len(users),50):
  cont=None
  while True:
   p={"action":"query","list":"usercontribs","ucuser":"|".join(users[i:i+50]),"ucstart":START.isoformat().replace("+00:00","Z"),"ucend":end.isoformat().replace("+00:00","Z"),"ucdir":"newer","uclimit":"max","ucnamespace":"0","ucprop":"ids|title|timestamp|comment|size|sizediff|flags|tags"}
   if cont:p["uccontinue"]=cont
   d=api(p);rows+=d["query"]["usercontribs"];cont=d.get("continue",{}).get("uccontinue")
   if not cont:break
 return rows
def build():
 now=datetime.now(timezone.utc);st=state(now);users=participants()
 base={"state":st,"participants":len(users),"active":0,"edits":0,"pages":0,"bytes":0,"new_articles":0,"people":[{"user":u,"edits":0,"pages":0,"bytes":0,"new_articles":0,"last":""} for u in users],"recent":[],"updated":(now+OFF).strftime("%Y-%m-%d %H:%M")}
 if st=="before" or not users:return base
 rows=contributions(users,min(now,END));by={u:[] for u in users}
 for r in rows:
  if r.get("user") in by:by[r["user"]].append(r)
 pages=set();people=[];recent=[];tb=tn=0
 for u in users:
  cs=by[u];ps={c["title"] for c in cs};b=sum(c.get("sizediff",0) for c in cs);n=sum(1 for c in cs if c.get("new"))
  pages|=ps;tb+=b;tn+=n
  for c in cs:
   dt=datetime.fromisoformat(c["timestamp"].replace("Z","+00:00"))+OFF
   recent.append({"user":u,"title":c["title"],"timestamp":c["timestamp"],"localtime":dt.strftime("%d %b %H:%M"),"sizediff":c.get("sizediff",0)})
  people.append({"user":u,"edits":len(cs),"pages":len(ps),"bytes":b,"new_articles":n,"last":max((c["timestamp"] for c in cs),default="")})
 people.sort(key=lambda x:x["last"],reverse=True);recent.sort(key=lambda x:x["timestamp"],reverse=True)
 base.update({"active":sum(p["edits"]>0 for p in people),"edits":len(rows),"pages":len(pages),"bytes":tb,"new_articles":tn,"people":people,"recent":recent[:40]});return base
def stats():
 if "d" not in cache or time.time()-cache["t"]>120:cache["d"]=build();cache["t"]=time.time()
 return cache["d"]
@app.route("/")
def home():return render_template("index.html")
@app.route("/api/stats")
def stats_api():
 try:return jsonify(stats())
 except Exception as e:app.logger.exception("stats");return jsonify({"error":str(e)}),500
@app.route("/api/task")
def task():
 try:
  label,cat=random.choice(TASKS);d=api({"action":"query","generator":"categorymembers","gcmtitle":"பகுப்பு:"+cat,"gcmnamespace":"0","gcmlimit":"50","prop":"info"});ps=d.get("query",{}).get("pages",[])
  if not ps:return jsonify({"error":"இந்தப் பகுப்பில் கட்டுரைகள் கிடைக்கவில்லை."}),404
  p=random.choice(ps);return jsonify({"task":label,"title":p["title"],"url":"https://ta.wikipedia.org/wiki/"+requests.utils.quote(p["title"].replace(" ","_"),safe="")})
 except Exception as e:return jsonify({"error":str(e)}),500
@app.route("/healthz")
def health():return "ok"
if __name__=="__main__":app.run(host="127.0.0.1",port=8000,debug=True)
