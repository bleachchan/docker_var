from flask import Flask, request, render_template_string
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
        .loading {
            display: none;
            color: yellow;
            margin-top: 10px;
        }
    </style>
</head>
<body>

<h2>💀 AUTO DORKER PARSIVAL</h2>

<form method="post" onsubmit="showLoading()">
<textarea name="dork">inurl:login
inurl:admin
dashboard
</textarea><br>

<button type="submit">▶ START</button>
<button type="button" onclick="clearResult()">🧹 CLEAR</button>
<button type="button" onclick="copyResult()">📋 COPY</button>

</form>

<div class="loading" id="loading">⚡ Scanning target...</div>

<h4>Total Target: <span id="count">0</span></h4>

<pre id="result">{{result}}</pre>

<script>
function clearResult(){
    document.getElementById("result").innerHTML = "";
    document.getElementById("count").innerText = 0;
}

function copyResult(){
    let text = document.getElementById("result").innerText;
    navigator.clipboard.writeText(text);
    alert("Copied!");
}

function showLoading(){
    document.getElementById("loading").style.display = "block";
}

window.onload = function(){
    let result = document.getElementById("result").innerText.trim();
    if(result){
        let lines = result.split("\\n").filter(x => x.trim() !== "");
        document.getElementById("count").innerText = lines.length;

        let box = document.getElementById("result");
        box.scrollTop = box.scrollHeight;
    }
}
</script>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    result = ""
    headers = {"User-Agent": "Mozilla/5.0"}

    if request.method == "POST":
        dorks = request.form["dork"].split("\\n")

        for dork in dorks:
            try:
                url = f"https://duckduckgo.com/html/?q={dork}"
                r = requests.get(url, headers=headers, timeout=10)

                soup = BeautifulSoup(r.text, "html.parser")

                for a in soup.find_all("a", href=True):
                    link = a["href"]

                    # ambil link asli dari redirect
                    if "uddg=" in link:
                        real = urllib.parse.parse_qs(
                            urllib.parse.urlparse(link).query
                        ).get("uddg")

                        if real:
                            result += real[0] + "\\n"

            except:
                result += f"[ERROR] {dork}\\n"

    return render_template_string(HTML, result=result)


if __name__ == "__main__":
    app.run(debug=True)
