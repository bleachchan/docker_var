from flask import Flask, request, render_template_string, jsonify
import requests, urllib.parse, random, re, time
from bs4 import BeautifulSoup

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
<title>Recon Pro Dashboard</title>
<style>
body {
    margin:0;
    font-family:Arial;
    background: linear-gradient(135deg,#2b1055,#1a2a6c);
    color:white;
}

/* HEADER */
.header {
    text-align:center;
    padding:30px;
}

input {
    width:60%;
    padding:15px;
    border-radius:30px;
    border:none;
    outline:none;
    font-size:16px;
}

/* BUTTON */
button {
    padding:10px 20px;
    margin:5px;
    border:none;
    border-radius:20px;
    background:#6a5acd;
    color:white;
    cursor:pointer;
}
button:hover {
    background:#7b68ee;
}

/* TABLE */
table {
    width:90%;
    margin:20px auto;
    border-collapse:collapse;
    background:rgba(0,0,0,0.3);
    border-radius:10px;
    overflow:hidden;
}
th, td {
    padding:10px;
    text-align:left;
}
th {
    background:#4b0082;
}
tr:nth-child(even) {
    background:rgba(255,255,255,0.05);
}
a {
    color:#8ab4f8;
    text-decoration:none;
}

/* BADGE */
.badge {
    padding:4px 8px;
    border-radius:6px;
    font-size:12px;
}
.ok { background:#4caf50; }
.err { background:#e53935; }
.login { background:#ff9800; }

.controls {
    text-align:center;
}
</style>
</head>
<body>

<div class="header">
    <h1>🔎 Recon Pro Dashboard</h1>
    <input id="q" placeholder='app="wordpress" && title="login"'>
    <br><br>
    <button onclick="start()">START</button>
    <button onclick="loadMore()">LOAD MORE</button>
    <button onclick="clearData()">CLEAR</button>
</div>

<div class="controls">
    Filter Status:
    <select id="filter" onchange="render()">
        <option value="all">All</option>
        <option value="200">200</option>
        <option value="403">403</option>
    </select>
</div>

<table>
<thead>
<tr>
<th>URL</th>
<th>Status</th>
<th>Type</th>
<th>Domain</th>
</tr>
</thead>
<tbody id="table"></tbody>
</table>

<div style="text-align:center;">
<img src="https://www.google.com/favicon.ico" onclick="loadMore()" style="width:40px;cursor:pointer;">
</div>

<script>
let page = 1;
let query = "";
let dataAll = [];

function start(){
    page = 1;
    dataAll = [];
    query = document.getElementById("q").value;
    fetchData();
}

function loadMore(){
    page++;
    fetchData();
}

function clearData(){
    dataAll = [];
    document.getElementById("table").innerHTML = "";
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
    let filter = document.getElementById("filter").value;
    let tbody = document.getElementById("table");
    tbody.innerHTML = "";

    dataAll.forEach(x=>{
        if(filter !== "all" && x.status != filter) return;

        let type = x.is_login ? 
            '<span class="badge login">LOGIN</span>' : 
            '<span class="badge">NORMAL</span>';

        let statusClass = x.status == 200 ? "ok" : "err";

        let row = `
        <tr>
            <td><a href="${x.url}" target="_blank">${x.url}</a></td>
            <td><span class="badge ${statusClass}">${x.status}</span></td>
            <td>${type}</td>
            <td>${x.domain}</td>
        </tr>`;
        tbody.innerHTML += row;
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
    is_login = any(x in url.lower() for x in ["login","admin"])

    return {"url":url,"status":status,"domain":domain,"is_login":is_login}

# ================= API =================
@app.route("/api",methods=["POST"])
def api():
    data=request.json
    q=data["q"]
    page=data.get("page",1)

    dorks=generate(q)
    results=[]

    for d in dorks[:5]:
        links=search(d,page)
        for l in links[:10]:
            results.append(analyze(l))
        time.sleep(0.5)

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
