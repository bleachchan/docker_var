from flask import Flask, request, render_template_string, jsonify, send_file
import requests, urllib.parse, random, re, time, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

# ================= CONFIG =================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Linux; Android 10)",
    "Mozilla/5.0 (iPhone)"
]

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<body style="background:#0d1117;color:#00ff9f;font-family:monospace;text-align:center;">

<h2>💀 ULTIMATE RECON</h2>

<textarea id="q" style="width:90%;height:120px;">
app="wordpress" && title="login"
</textarea><br>

<button onclick="start()">START</button>
<button onclick="save()">SAVE</button>

<pre id="out"></pre>

<script>
let results = [];

function start(){
 fetch("/api", {
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body: JSON.stringify({q:document.getElementById("q").value})
 })
 .then(r=>r.json())
 .then(d=>{
   results = d;
   document.getElementById("out").innerText =
     d.map(x=>x.url + " | " + x.status).join("\\n");
 });
}

function save(){
 window.location = "/save";
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
    data = {}
    for k in ["app","title","body"]:
        m = re.search(fr'{k}="([^"]+)"', q)
        if m:
            data[k] = m.group(1)
    return data

# ================= GENERATE =================
def generate(q):
    parsed = parse_fofa(q)
    dorks = []

    if not parsed:
        return q.split("\\n")

    if "app" in parsed:
        app = parsed["app"]
        dorks += [f"{app} login", f"{app} admin"]

    if "title" in parsed:
        dorks.append(f'intitle:{parsed["title"]}')

    if "body" in parsed:
        clean = parsed["body"].split("?")[0]
        dorks += [clean, f'inurl:{clean}']

    return list(set(dorks))

# ================= SEARCH =================
def search(dork):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text,"html.parser")
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
        r = requests.head(url, timeout=3)
        status = r.status_code
    except:
        status = 0

    parsed = urlparse(url)

    return {
        "url": url,
        "domain": parsed.netloc,
        "path": parsed.path,
        "status": status,
        "is_login": any(x in url.lower() for x in ["login","admin"])
    }

# ================= API =================
DATA_CACHE = []

@app.route("/api", methods=["POST"])
def api():
    global DATA_CACHE

    q = request.json["q"]
    dorks = generate(q)

    results = []

    for d in dorks[:5]:
        links = search(d)
        for l in links[:10]:
            results.append(analyze(l))
        time.sleep(1)

    # dedup
    seen=set()
    clean=[]
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            clean.append(r)

    DATA_CACHE = clean
    return jsonify(clean)

# ================= SAVE =================
@app.route("/save")
def save():
    global DATA_CACHE
    with open("result.json","w") as f:
        json.dump(DATA_CACHE,f,indent=2)

    return send_file("result.json", as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
