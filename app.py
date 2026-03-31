from flask import Flask, request, render_template_string, jsonify
import requests, urllib.parse, random, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Linux; Android 10)",
    "Mozilla/5.0 (iPhone)"
]

MAX_THREADS = 10  # jumlah parallel request

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>HIGH SPEED RECON ENGINE</title>
<style>
body{margin:0;font-family:Arial;background:linear-gradient(135deg,#2b1055,#1a2a6c);color:white;}
.header{text-align:center;padding:20px;}
input{width:60%;padding:12px;border-radius:30px;border:none;font-size:16px;}
button{padding:10px 20px;margin:5px;border:none;border-radius:20px;background:#6a5acd;color:white;}
table{width:95%;margin:20px auto;border-collapse:collapse;}
th,td{padding:8px;}
th{background:#4b0082;}
tr:nth-child(even){background:rgba(255,255,255,0.05);}
a{color:#8ab4f8;}
.badge{padding:3px 6px;border-radius:6px;font-size:12px;}
.ok{background:#4caf50;}
.err{background:#e53935;}
.match{background:#ff9800;}
</style>
</head>
<body>

<div class="header">
<h2>⚡ HIGH SPEED RECON ENGINE</h2>
<input id="q" placeholder='app="wordpress" && body="business/register"'>
<br>
<button onclick="start()">START</button>
<button onclick="clearData()">CLEAR</button>
</div>

<table>
<thead>
<tr>
<th>URL</th>
<th>Status</th>
<th>Login</th>
<th>Match</th>
<th>Domain</th>
</tr>
</thead>
<tbody id="table"></tbody>
</table>

<script>
let dataAll=[];
function start(){
    dataAll=[];
    let query=document.getElementById("q").value;
    fetch("/api",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({q:query})})
    .then(r=>r.json())
    .then(data=>{
        dataAll=data;
        render();
    });
}

function clearData(){
    dataAll=[];
    document.getElementById("table").innerHTML="";
}

function render(){
    let t=document.getElementById("table");
    t.innerHTML="";
    dataAll.forEach(x=>{
        let login=x.is_login?'<span class="badge ok">YES</span>':'NO';
        let match=x.match?'<span class="badge match">YES</span>':'NO';
        let statusClass=x.status==200?"ok":"err";
        t.innerHTML+=`<tr>
<td><a href="${x.url}" target="_blank">${x.url}</a></td>
<td><span class="badge ${statusClass}">${x.status}</span></td>
<td>${login}</td>
<td>${match}</td>
<td>${x.domain}</td>
</tr>`;
    });
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

# ================= FOFA PARSER =================
def parse_fofa(q):
    data={}
    for k in ["app","title","body"]:
        m=re.search(fr'{k}="([^"]+)"',q)
        if m: data[k]=m.group(1)
    return data

# ================= GENERATE DORK =================
def generate(q):
    parsed=parse_fofa(q)
    dorks=[]
    if not parsed: return q.split("\\n")
    if "app" in parsed:
        a=parsed["app"]
        dorks += [f"{a} login", f"{a} admin"]
    if "title" in parsed:
        dorks.append(f'intitle:{parsed["title"]}')
    if "body" in parsed:
        body = parsed["body"]
        clean = body.split("?")[0]
        words = re.split(r'[\W_]+', clean)
        dorks += [f'"{body}"', f'"{clean}"', clean, f'inurl:{clean}']
        for w in words:
            if len(w)>3:
                dorks += [w, f'inurl:{w}', f'intitle:{w}']
    return list(set(dorks))

# ================= SEARCH MULTI ENGINE =================
def search(dork):
    results=[]
    engines=[
        f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}",
        f"https://www.bing.com/search?q={urllib.parse.quote(dork)}"
    ]
    for url in engines:
        try:
            r=requests.get(url, headers={"User-Agent": random.choice(UA)}, timeout=5)
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.find_all("a",href=True):
                h=a["href"]
                if "uddg=" in h:
                    real=urllib.parse.parse_qs(urllib.parse.urlparse(h).query).get("uddg")
                    if real: results.append(real[0])
                elif h.startswith("http"):
                    results.append(h)
        except: pass
    return list(set(results))

# ================= ANALYZE URL =================
def analyze(url):
    try:
        r=requests.head(url,timeout=3)
        status=r.status_code
    except:
        status=0
    domain=urllib.parse.urlparse(url).netloc
    is_login=any(x in url.lower() for x in ["login","admin"])
    return {"url":url,"status":status,"domain":domain,"is_login":is_login}

# ================= CONTENT SCANNER =================
def content_match(url,patterns):
    try:
        r=requests.get(url,timeout=5)
        text=r.text.lower()
        for p in patterns:
            if p.lower() in text:
                return True
    except: pass
    return False

# ================= CRAWLER =================
def crawl(url,patterns,limit=10):
    found=[]
    try:
        r=requests.get(url,timeout=5)
        soup=BeautifulSoup(r.text,"html.parser")
        links=[urljoin(url,a["href"]) for a in soup.find_all("a",href=True)]
        for link in links[:limit]:
            if content_match(link,patterns):
                found.append(link)
    except: pass
    return found

# ================= WORKER THREAD =================
def process_link(url, patterns):
    data = analyze(url)
    if patterns:
        data["match"] = content_match(url, patterns)
        if not data["match"]:
            crawled = crawl(url, patterns, limit=10)
            if crawled:
                data["match"]=True
    else:
        data["match"]=False
    return data

# ================= API =================
@app.route("/api",methods=["POST"])
def api():
    data=request.json
    q=data["q"]
    dorks=generate(q)

    patterns=[]
    parsed=parse_fofa(q)
    if "body" in parsed: patterns.append(parsed["body"])

    all_links=[]
    for d in dorks[:10]:
        all_links += search(d)

    # multi-thread
    results=[]
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures=[executor.submit(process_link, url, patterns) for url in all_links[:100]]
        for f in futures:
            results.append(f.result())

    # dedup
    seen=set()
    clean=[]
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            clean.append(r)

    return jsonify(clean[:100])

# ================= RUN =================
if __name__=="__main__":
    app.run(debug=True)
