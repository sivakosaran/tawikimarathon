from flask import Flask,render_template,jsonify,request
import requests,random,time
from datetime import datetime,timezone,timedelta
app=Flask(__name__)
API="https://ta.wikipedia.org/w/api.php"; PAGE="விக்கிப்பீடியா:விக்கி மாரத்தான் 2026"
START=datetime(2026,9,27,0,30,tzinfo=timezone.utc); END=datetime(2026,9,28,0,30,tzinfo=timezone.utc); OFF=timedelta(hours=5,minutes=30)
UA="TamilWikiMarathonDashboard/2.1.2 (https://github.com/sivakosaran/tawikimarathon; User:Sivakosaran)"
TASKS=[("மேற்கோள் சேர்த்தல்","சான்றுகள் தேவைப்படும் அனைத்துக் கட்டுரைகள்"),("பகுப்பு சேர்த்தல்","பகுப்பில்லாதவை"),("விக்கியாக்கம்","விக்கிப்படுத்தப்பட வேண்டிய கட்டுரைகள்"),("குறுங்கட்டுரைகளை விரிவாக்குதல்","குறுங்கட்டுரைகள்")]
S=requests.Session(); S.headers.update({"User-Agent":UA}); cache={}
def api(p):
 r=S.get(API,params={**p,"format":"json","formatversion":2,"maxlag":5},timeout=20); r.raise_for_status(); d=r.json()
 if "error" in d: raise RuntimeError(d["error"].get("info","MediaWiki API error"))
 return d
def participants():
 ss=api({"action":"parse","page":PAGE,"prop":"sections"})["parse"]["sections"]; idx=next((s["index"] for s in ss if "பங்களிக்க விரும்புபவர்கள்" in s.get("line","")),None)
 if idx is None:return []
 ls=api({"action":"parse","page":PAGE,"section":idx,"prop":"links"})["parse"].get("links",[])
 return sorted(set(x["title"].split(":",1)[1] for x in ls if x.get("ns")==2 and ":" in x.get("title","")),key=str.casefold)
def state(n):return "before" if n<START else ("finished" if n>=END else "live")
def contributions(users,end):
 rows=[]
 for i in range(0,len(users),50):
  cont=None
  while True:
   p={"action":"query","list":"usercontribs","ucuser":"|".join(users[i:i+50]),"ucstart":START.isoformat().replace("+00:00","Z"),"ucend":end.isoformat().replace("+00:00","Z"),"ucdir":"newer","uclimit":"max","ucnamespace":"0","ucprop":"ids|title|timestamp|sizediff|flags"}
   if cont:p["uccontinue"]=cont
   d=api(p); rows+=d["query"]["usercontribs"]; cont=d.get("continue",{}).get("uccontinue")
   if not cont:break
 return rows
def build():
 now=datetime.now(timezone.utc); st=state(now); users=participants()
 b={"state":st,"participants":len(users),"active":0,"edits":0,"pages":0,"bytes":0,"new_articles":0,"people":[{"user":u,"edits":0,"pages":0,"bytes":0,"new_articles":0} for u in users],"recent":[],"hourly":[0]*24,"updated":(now+OFF).strftime("%Y-%m-%d %H:%M")}
 if st=="before" or not users:return b
 rows=contributions(users,min(now,END)); by={u:[] for u in users}
 for r in rows:
  if r.get("user") in by:by[r["user"]].append(r)
  h=int((datetime.fromisoformat(r["timestamp"].replace("Z","+00:00"))-START).total_seconds()//3600)
  if 0<=h<24:b["hourly"][h]+=1
 pages=set(); people=[]; recent=[]; totalbytes=totalnew=0
 for u in users:
  cs=by[u]; ps={c["title"] for c in cs}; bd=sum(c.get("sizediff",0) for c in cs); new=sum(1 for c in cs if c.get("new")); pages|=ps; totalbytes+=bd; totalnew+=new
  for c in cs:
   dt=datetime.fromisoformat(c["timestamp"].replace("Z","+00:00"))+OFF; recent.append({"user":u,"title":c["title"],"timestamp":c["timestamp"],"localtime":dt.strftime("%d %b %H:%M"),"sizediff":c.get("sizediff",0)})
  people.append({"user":u,"edits":len(cs),"pages":len(ps),"bytes":bd,"new_articles":new,"last":max((c["timestamp"] for c in cs),default="")})
 people.sort(key=lambda x:x.get("last",""),reverse=True); recent.sort(key=lambda x:x["timestamp"],reverse=True)
 b.update({"active":sum(p["edits"]>0 for p in people),"edits":len(rows),"pages":len(pages),"bytes":totalbytes,"new_articles":totalnew,"people":people,"recent":recent[:40]}); return b
def stats():
 if "d" not in cache or time.time()-cache["t"]>120:cache["d"]=build(); cache["t"]=time.time()
 return cache["d"]
@app.route("/")
def home():return render_template("index.html")
@app.route("/api/stats")
def stats_api():
 try:return jsonify(stats())
 except Exception as e:return jsonify({"error":str(e)}),500
TASK_CACHE_SECONDS=600
task_cache={"at":0,"pools":{}}
recent_tasks=[]

CITATION_CATEGORY="சான்றுகள் தேவைப்படும் அனைத்துக் கட்டுரைகள்"

def category_members(category, namespace, limit=500):
    items=[]; cont=None
    while len(items)<limit:
        params={"action":"query","list":"categorymembers","cmtitle":"பகுப்பு:"+category,
                "cmnamespace":str(namespace),"cmlimit":"max","cmprop":"title"}
        if cont: params["cmcontinue"]=cont
        d=api(params)
        items.extend(x["title"] for x in d.get("query",{}).get("categorymembers",[]))
        cont=d.get("continue",{}).get("cmcontinue")
        if not cont: break
    return items[:limit]

def citation_task_pool():
    """Use articles in the citation parent category and its immediate subcategories."""
    pages=category_members(CITATION_CATEGORY,0,500)
    subcats=category_members(CITATION_CATEGORY,14,100)
    random.shuffle(subcats)
    # Pull articles from every child category, with a generous overall cap.
    for fullcat in subcats:
        cat=fullcat.split(":",1)[1] if ":" in fullcat else fullcat
        pages.extend(category_members(cat,0,500))
        if len(pages)>=3000: break
    return list(dict.fromkeys(pages))

def task_pool(category):
    now=time.time()
    if now-task_cache["at"]>TASK_CACHE_SECONDS:
        task_cache["pools"]={}; task_cache["at"]=now
    if category in task_cache["pools"]:
        return task_cache["pools"][category]
    if category==CITATION_CATEGORY:
        pages=citation_task_pool()
    else:
        pages=category_members(category,0,500)
    task_cache["pools"][category]=pages
    return pages

@app.route("/api/task")
def task():
    wanted=request.args.get("type","")
    ordered=[t for t in TASKS if t[1]==wanted] if wanted else TASKS[:]
    if wanted and not ordered:return jsonify({"error":"தவறான பணி வகை."}),400
    if not wanted: random.shuffle(ordered)
    else:
        # Chosen category first; silently fall back to other task types if empty.
        others=[t for t in TASKS if t[1]!=wanted]; random.shuffle(others); ordered+=others
    for label,cat in ordered:
        try:
            pool=task_pool(cat)
        except Exception:
            app.logger.exception("Task category failed: %s",cat)
            continue
        if not pool: continue
        fresh=[title for title in pool if title not in recent_tasks]
        title=random.choice(fresh or pool)
        recent_tasks.append(title)
        if len(recent_tasks)>30: del recent_tasks[:-30]
        return jsonify({"task":label,"title":title,
            "url":"https://ta.wikipedia.org/wiki/"+requests.utils.quote(title.replace(" ","_"),safe=""),
            "fallback":bool(wanted and cat!=wanted)})
    return jsonify({"error":"தற்போது பணிக்கான கட்டுரைகளைப் பெற முடியவில்லை. சிறிது நேரம் கழித்து மீண்டும் முயலுங்கள்."}),503

@app.route("/healthz")
def health():return "ok"
if __name__=="__main__":app.run(host="127.0.0.1",port=8000,debug=True)
