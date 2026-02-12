from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AUTH = "http://auth-service:5000"
SPIDER = "http://spider-service:5000"
ANALYSIS = "http://analysis-service:5000"
RECOMMEND = "http://recommend-service:5000"

def proxy(url):
    if request.method == "GET":
        r = requests.get(url, params=request.args)
    else:
        r = requests.post(url, json=request.json)
    return jsonify(r.json()), r.status_code

@app.route('/api/login', methods=['POST'])
def login(): return proxy(f"{AUTH}/login")

@app.route('/api/register', methods=['POST'])
def register(): return proxy(f"{AUTH}/register")

@app.route('/api/spider/start', methods=['POST'])
def spider_start(): return proxy(f"{SPIDER}/start")

@app.route('/api/spider/status')
def spider_status(): return proxy(f"{SPIDER}/status")

@app.route('/api/analysis/city')
def city_analysis(): return proxy(f"{ANALYSIS}/city")

@app.route('/api/recommend')
def recommend(): return proxy(f"{RECOMMEND}/recommend")
