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
dashboard</textarea><br>

<button type="submit">▶ START</button>
<button type="button" onclick="clearResult()">🧹 CLEAR</button>
<button type="button" onclick="copyResult()">📋 COPY</button>

</form>

<div class="loading" id="loading">⚡ Scanning target...</div>

<h4>Total Target: {{count}}</h4>

<pre id="result">{{result}}</pre>

<div style="margin-top:10px;">
    {% if has_prev %}
        <a href="?page={{page-1}}"><button>⬅ Prev</button></a>
    {% endif %}

    {% if has_next %}
        <a href="?page={{page+1}}"><button>Next ➡</button></
