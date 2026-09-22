from flask import Flask,render_template,jsonify
import requests,random,time
from datetime import datetime,timezone,timedelta
app=Flask(__name__)
API="https://ta.wikipedia.org/w/api.php"; PAGE="விக்கிப்பீடியா:விக்கி மாரத்தான் 2026"
START=datetime(2026,9,27,0,30,tzinfo=timezone.utc); END=datetime(2026,9,28,0,30,tzinfo=timezone.utc); OFF=timedelta(hours=5,minutes=30)
UA="TamilWikiMarathonDashboard/1.0 (Wikimedia Toolforge)"
TASKS=[("கூகுள் தமிழாக்கக் கட்டுரைகளைச் செம்மைப்படுத்தல்","கூகுள் தமிழாக்கக் கட்டுரைகள்"),("மேற்கோள் சேர்த்தல்","சான்றுகள் தேவைப்படும் அனைத்துக் கட்டுரைகள்"),("பகுப்பு சேர்த்தல்","பகுப்பில்லாதவை"),("விக்கியாக்கம்","விக்கிப்படுத்தப்பட வேண்டிய கட்டுரைகள்"),("குறுங்கட்டுரைகளை விரிவாக்குதல்","குறுங்கட்டுரைகள்")]
cache={}
def api(p):
 p={**p,"format":"json","formatversion":2}; r=requests.get(API,params=p,headers={"User-Agent":UA},timeout=30); r.raise_for_status(); return r.json()
def participants():
 ss=api({"action":"parse","page":PAGE,"prop":"sections"})["parse"]["sections"]; idx=next((s["index"] for s in ss if "பங்களிக்க விரும்புபவர்கள்" in s.get("line","")),None)
 if idx is None:return []
 links=api({"action":"parse","page":PAGE,"section":idx,"prop":"links"})["parse"].get("links",[])
 return sorted(set(x["title"].split(":",1)[1] for x in links if x.get("ns")==2 and ":" in x["title"]),key=str.casefold)
def contribs(u):
 out=[]; cont=None
 while True:
  p={"action":"query","list":"usercontribs","ucuser":u,"ucstart":START.isoformat().replace("+00:00","Z"),"ucend":END.isoformat().replace("+00:00","Z"),"ucdir":"newer","uclimit":"max","ucnamespace":"0","ucprop":"ids|title|timestamp|comment|size|sizediff|flags|tags"}
  if cont:p["uccontinue"]=cont
  d=api(p); out+=d["query"]["usercontribs"]; cont=d.get("continue",{}).get("uccontinue")
  if not cont:return out
def build():
 users=participants(); people=[]; recent=[]; pages=set(); edits=bytes_=new=0; now=min(datetime.now(timezone.utc),END)
 for u in users:
  cs=[c for c in contribs(u) if START<=datetime.fromisoformat(c["timestamp"].replace("Z","+00:00"))<=now]; ps={c["title"] for c in cs}; b=sum(c.get("sizediff",0) for c in cs); n=sum(1 for c in cs if c.get("new"))
  edits+=len(cs);bytes_+=b;new+=n;pages|=ps
  for c in cs:
   c={**c,"user":u,"localtime":(datetime.fromisoformat(c["timestamp"].replace("Z","+00:00"))+OFF).strftime("%H:%M")};recent.append(c)
  people.append({"user":u,"edits":len(cs),"pages":len(ps),"bytes":b,"new_articles":n,"last":max((c["timestamp"] for c in cs),default="")})
 people.sort(key=lambda x:x["last"],reverse=True);recent.sort(key=lambda x:x["timestamp"],reverse=True)
 return {"participants":len(users),"active":sum(p["edits"]>0 for p in people),"edits":edits,"pages":len(pages),"bytes":bytes_,"new_articles":new,"people":people,"recent":recent[:30],"updated":(datetime.now(timezone.utc)+OFF).strftime("%Y-%m-%d %H:%M")}
def stats():
 if "d" not in cache or time.time()-cache["t"]>120:cache["d"]=build();cache["t"]=time.time()
 return cache["d"]
@app.route("/")
def home():return render_template("index.html",s=stats())
@app.route("/api/stats")
def api_stats():return jsonify(stats())
@app.route("/api/task")
def task():
 label,cat=random.choice(TASKS);d=api({"action":"query","generator":"categorymembers","gcmtitle":"பகுப்பு:"+cat,"gcmnamespace":"0","gcmlimit":"50","prop":"info"});ps=d.get("query",{}).get("pages",[])
 if not ps:return jsonify({"error":"கட்டுரை கிடைக்கவில்லை"}),404
 p=random.choice(ps);return jsonify({"task":label,"title":p["title"],"url":"https://ta.wikipedia.org/wiki/"+requests.utils.quote(p["title"].replace(" ","_"),safe="")})
@app.route("/healthz")
def health():return "ok"
