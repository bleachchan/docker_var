from flask import Flask, request, render_template_string, jsonify
import requests, urllib.parse, random, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Linux; Android 10)",
    "Mozilla/5.0 (iPhone)"
]

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Recon Ultimate</title>
<style>
body {
    margin:0;
    font-family:Arial;
    background: linear-gradient(135deg,#2b1055,#1a2a6c);
    color:white;
}
.header { text-align:center; padding:20px; }
input {
    width:60%; padding:12px; border-radius:30px;
    border:none; font-size:16px;
}
button {
    padding:10px 20px; margin:5px;
    border:none; border-radius:20px;
    background:#6a5acd; color:white;
}
table {
    width:95%; margin:20px auto;
    border-collapse:collapse;
}
th,td { padding:8px; }
th { background:#4b0082; }
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
<h2>💀 Recon Ultimate (Scanner + Crawler)</h2>
<input id="q" placeholder='app="wordpress" && body="business/register"'>
<br>
<button onclick="start()">START</button>
<button onclick="loadMore()">LOAD MORE</button>
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
let page=1,query="",dataAll=[];

function start(){
    page=1;
    dataAll=[];
    query=document.getElementById("q").value;
    fetchData();
}

function loadMore(){
    page++;
    fetchData();
}

function clearData(){
    dataAll=[];
    document.getElementById("table").innerHTML="";
}

function fetchData(){
    fetch("/api",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({q:query,page:page})
    })
    .then(r=>r.json())
    .then(data=>{
        data.forEach(x=>{
            if(!dataAll.find(y=>y.url===x.url)){
                dataAll.push(x);
            }
        });
        render();
    });
}

function render(){
    let t=document.getElementById("table");
    t.innerHTML="";

    dataAll.forEach(x=>{
        let login=x.is_login?'<span class="badge ok">YES</span>':'NO';
        let match=x.match?'<span class="badge match">YES</span>':'NO';
        let statusClass=x.status==200?"ok":"err";

        t.innerHTML+=`
        <tr>
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

# ================= GENERATE =================
def generate(q):
    parsed=parse_fofa(q)
    dorks=[]

    if not parsed:
        return q.split("\\n")

    if "app" in parsed:
        a=parsed["app"]
        dorks += [f"{a} login",f"{a} admin"]

    if "title" in parsed:
        dorks.append(f'intitle:{parsed["title"]}')

    if "body" in parsed:
        clean=parsed["body"].split("?")[0]
        dorks += [clean,f'inurl:{clean}']

    return list(set(dorks))

# ================= SEARCH =================
def search(dork,page):
    start=(page-1)*20
    url=f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}&s={start}"

    try:
        r=requests.get(url,headers={"User-Agent":random.choice(UA)},timeout=5)
        soup=BeautifulSoup(r.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            h=a["href"]
            if "uddg=" in h:
                real=urllib.parse.parse_qs(
                    urllib.parse.urlparse(h).query
                ).get("uddg")
                if real: links.append(real[0])
        return links
    except:
        return []

# ================= ANALYZE =================
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
    except:
        pass
    return False

# ================= CRAWLER =================
def crawl(url,patterns,limit=3):
    found=[]
    try:
        r=requests.get(url,timeout=5)
        soup=BeautifulSoup(r.text,"html.parser")

        links=[urljoin(url,a["href"]) for a in soup.find_all("a",href=True)]

        for link in links[:limit]:
            if content_match(link,patterns):
                found.append(link)
    except:
        pass
    return found

# ================= API =================
@app.route("/api",methods=["POST"])
def api():
    data=request.json
    q=data["q"]
    page=data.get("page",1)

    parsed=parse_fofa(q)
    dorks=generate(q)

    patterns=[]
    if "body" in parsed:
        patterns.append(parsed["body"])

    results=[]

    for d in dorks[:5]:
        links=search(d,page)

        for l in links[:8]:
            data=analyze(l)

            # content scan
            if patterns:
                data["match"]=content_match(l,patterns)
            else:
                data["match"]=False

            # crawler scan
            if not data["match"] and patterns:
                crawled=crawl(l,patterns)
                if crawled:
                    data["match"]=True

            results.append(data)

        time.sleep(0.5)

    # dedup
    seen=set()
    clean=[]
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            clean.append(r)

    return jsonify(clean[:40])

# ================= RUN =================
if __name__=="__main__":
    app.run(debug=True)
