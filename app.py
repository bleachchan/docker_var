from flask import Flask, request, render_template_string, jsonify
import requests, urllib.parse, random, json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

UA = ["Mozilla/5.0","Mozilla/5.0 (Linux; Android 10)"]
MAX_THREADS = 30

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>FINAL BOSS RECON</title>
<style>
body{background:linear-gradient(135deg,#2b1055,#1a2a6c);color:white;font-family:Arial;text-align:center;}
input{width:60%;padding:12px;border-radius:30px;border:none;}
button{padding:10px 20px;margin:10px;border:none;border-radius:20px;background:#6a5acd;color:white;}
table{width:90%;margin:auto;border-collapse:collapse;}
th,td{padding:8px;}
th{background:#4b0082;}
tr:nth-child(even){background:rgba(255,255,255,0.05);}
</style>
</head>
<body>

<h2>💀 FINAL BOSS RECON ENGINE</h2>

<input id="q" placeholder="example.com atau keyword">
<br>
<button onclick="start()">START SCAN</button>

<table>
<thead>
<tr>
<th>Domain</th>
<th>Status</th>
<th>CMS</th>
<th>Score</th>
</tr>
</thead>
<tbody id="table"></tbody>
</table>

<script>
function start(){
fetch("/api",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({q:document.getElementById("q").value})})
.then(r=>r.json())
.then(data=>{
let t=document.getElementById("table");
t.innerHTML="";
data.forEach(x=>{
t.innerHTML+=`
<tr>
<td>${x.domain}</td>
<td>${x.status}</td>
<td>${x.cms}</td>
<td>${x.score}</td>
</tr>`;
});
});
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

# ================= SUBDOMAIN DISCOVERY =================
def find_subdomains(domain):
    subs=set()

    try:
        r=requests.get(f"https://crt.sh/?q={domain}&output=json",timeout=5)
        data=r.json()
        for entry in data:
            name=entry["name_value"]
            for d in name.split("\n"):
                if domain in d:
                    subs.add(d.strip())
    except:
        pass

    return list(subs)

# ================= CMS DETECT =================
def detect_cms(url):
    try:
        r=requests.get(url,timeout=5)
        text=r.text.lower()

        if "wp-content" in text:
            return "WordPress",70
        if "laravel" in text or "_token" in text:
            return "Laravel",60
        if "elfinder" in text:
            return "elFinder",80

    except:
        pass

    return "Unknown",10

# ================= ANALYZE =================
def analyze(domain):
    url="http://"+domain

    try:
        r=requests.get(url,timeout=5)
        status=r.status_code
    except:
        status=0

    cms,score=detect_cms(url)

    return {
        "domain":domain,
        "status":status,
        "cms":cms,
        "score":score
    }

# ================= API =================
@app.route("/api",methods=["POST"])
def api():
    data=request.json
    q=data["q"]

    targets=[]

    if "." in q:
        targets=find_subdomains(q)
        targets.append(q)
    else:
        targets=[q]

    results=[]

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        results=list(ex.map(analyze,targets))

    return jsonify(results)

# ================= RUN =================
if __name__=="__main__":
    app.run(debug=True)
