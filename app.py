from flask import Flask, request, render_template_string, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import random
import re

app = Flask(__name__)

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FOFA Smart Dorker</title>
</head>
<body style="background:#0d1117;color:#00ff9f;font-family:monospace;text-align:center;padding:20px;">

<h2>💀 FOFA SMART DORKER</h2>

<textarea id="dork" style="width:90%;height:120px;background:#161b22;color:#00ff9f;border:1px solid #00ff9f;padding:10px;">
app="wordpress" && title="login"
</textarea><br>

<button onclick="start()">▶ START</button>
<button onclick="loadMore()">➕ LOAD MORE</button>
<button onclick="clearResult()">🧹 CLEAR</button>
<button onclick="copyResult()">📋 COPY</button>

<h4>Total Target: <span id="count">0</span></h4>

<pre id="result" style="background:black;padding:10px;max-height:300px;overflow:auto;"></pre>

<script>
let page = 1;
let allResults = [];

function start(){
    page = 1;
    allResults = [];
    document.getElementById("result").innerHTML = "";
    document.getElementById("count").innerText = 0;
    fetchData();
}

function loadMore(){
    page++;
    fetchData();
}

function fetchData(){
    let dork = document.getElementById("dork").value;

    fetch("/api", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({dork: dork, page: page})
    })
    .then(res => res.json())
    .then(data => {
        allResults = [...new Set([...allResults, ...data.results])];

        document.getElementById("result").innerText = allResults.join("\\n");
        document.getElementById("count").innerText = allResults.length;
    });
}

function clearResult(){
    document.getElementById("result").innerHTML = "";
    document.getElementById("count").innerText = 0;
    allResults = [];
}

function copyResult(){
    navigator.clipboard.writeText(document.getElementById("result").innerText);
    alert("Copied!");
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

# ================= FOFA PARSER =================
def parse_fofa(query):
    data = {}

    patterns = {
        "app": r'app="([^"]+)"',
        "title": r'title="([^"]+)"',
        "body": r'body="([^"]+)"'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, query)
        if match:
            data[key] = match.group(1)

    return data

# ================= DORK GENERATOR =================
def generate_dorks(parsed, raw):
    dorks = []

    # jika bukan FOFA → pakai langsung
    if not parsed:
        return raw.split("\\n")

    # app logic
    if "app" in parsed:
        app = parsed["app"]

        dorks += [
            f"{app} login",
            f"{app} admin",
            f"{app} dashboard"
        ]

        if "wordpress" in app.lower():
            dorks += [
                "wordpress wp-login",
                "wordpress wp-admin"
            ]

    # title
    if "title" in parsed:
        dorks.append(f'intitle:{parsed["title"]}')

    # body
    if "body" in parsed:
        dorks.append(f'"{parsed["body"]}"')

    return dorks

# ================= FILTER =================
def is_interesting(url):
    keywords = ["login", "admin", "dashboard", "signin", "panel"]
    return any(k in url.lower() for k in keywords)

# ================= EXTRACT =================
def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "uddg=" in href:
            real = urllib.parse.parse_qs(
                urllib.parse.urlparse(href).query
            ).get("uddg")

            if real:
                links.append(real[0])

        elif href.startswith("http"):
            links.append(href)

    return links

# ================= API =================
@app.route("/api", methods=["POST"])
def api():
    data = request.get_json()
    raw_query = data["dork"]
    page = data.get("page", 1)

    parsed = parse_fofa(raw_query)
    dorks = generate_dorks(parsed, raw_query)

    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Linux; Android 10)",
            "Mozilla/5.0 (iPhone)"
        ])
    }

    results = []

    for dork in dorks[:5]:
        try:
            start = (page - 1) * 30
            url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}&s={start}"

            r = requests.get(url, headers=headers, timeout=5)
            links = extract_links(r.text)

            filtered = [x for x in links if is_interesting(x)]
            results += filtered

        except:
            pass

    # dedup
    clean = []
    for x in results:
        if x not in clean:
            clean.append(x)

    return jsonify({"results": clean[:50]})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
