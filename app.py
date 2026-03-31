from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML = """
<h2>Auto Dorker</h2>
<form method="post">
<textarea name="dork" rows="5" cols="50">"Dash SaaS" inurl:login</textarea><br>
<button type="submit">Start</button>
</form>
<pre>{{result}}</pre>
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
