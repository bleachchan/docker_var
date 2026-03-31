from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

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
            margin: 10px;
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

<form method="post">
<textarea name="dork">"Dash SaaS" inurl:login
"WorkDo" inurl:dashboard</textarea><br>
<button type="submit">▶ START</button>
<button type="button" onclick="clearResult()">🧹 CLEAR</button>
</form>

<pre id="result">{{result}}</pre>

<script>
function clearResult(){
    document.getElementById("result").innerHTML = "";
}
</script>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    result = ""
    if request.method == "POST":
        dorks = request.form["dork"].split("\\n")
        for dork in dorks:
            r = requests.post(f"https://html.duckduckgo.com/html/?q={dork}")
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.result__a"):
                link = a.get("href")
                if link:
                    result += link + "\\n"
    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    app.run(debug=True)
