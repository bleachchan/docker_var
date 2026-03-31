from flask import Flask, request, render_template_string, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dorker Pro</title>
    <style>
        body {
            background: #0d1117;
            color: #00ff9f;
            font-family: monospace;
            text-align: center;
            padding: 20px;
        }
        textarea {
            width: 90%;
            height: 120px;
            background: #161b22;
            color: #00ff9f;
            border: 1px solid #00ff9f;
            padding: 10px;
        }
        button {
            background: #00ff9f;
            color: black;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: #00cc7a;
        }
        pre {
            background: black;
            color: #00ff9f;
            padding: 10px;
            text-align: left;
            max-height: 300px;
            overflow: auto;
            border: 1px solid #00ff9f;
        }
    </style>
</head>
<body>

<h2>💀 AUTO DORKER PARSIVAL</h2>

<textarea id="dork">inurl:login
inurl:admin
dashboard</textarea><br>

<button onclick="start()">▶ START</button>
<button onclick="loadMore()">➕ LOAD MORE</button>
<button onclick="clearResult()">🧹 CLEAR</button>
<button onclick="copyResult()">📋 COPY</button>

<h4>Total Target: <span id="count">0</span></h4>

<pre id="result"></pre>

<script>
let page = 1;
let allResults = [];

function start(){
    page = 1;
    allResults = [];
    document.getElementById("result").innerHTML = "";
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

        let box = document.getElementById("result");
        box.scrollTop = box.scrollHeight;
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


@app.route("/api", methods=["POST"])
def api():
    data = request.get_json()
    dorks = data["dork"].split("\\n")
    page = int(data.get("page", 1))

    headers = {"User-Agent": "Mozilla/5.0"}
    result_list = []

    MAX_RESULTS = 30  # per load

    for dork in dorks[:5]:
        try:
            url = f"https://duckduckgo.com/html/?q={dork}&s={(page-1)*30}"
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                link = a["href"]

                if "uddg=" in link:
                    real = urllib.parse.parse_qs(
                        urllib.parse.urlparse(link).query
                    ).get("uddg")

                    if real:
                        result_list.append(real[0])

                        if len(result_list) >= MAX_RESULTS:
                            break

        except:
            pass

    return jsonify({"results": result_list})


if __name__ == "__main__":
    app.run(debug=True)
