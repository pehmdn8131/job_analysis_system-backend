from flask import Flask, request, jsonify
from threading import Thread
from spider import run_spider_task
from status import spider_status

app = Flask(__name__)

@app.route('/start', methods=['POST'])
def start():
    kw = request.json.get("keyword")
    if spider_status['is_running']: return jsonify({"msg":"running"})
    Thread(target=run_spider_task,args=(kw,1)).start()
    return jsonify({"msg":"started"})

@app.route('/status')
def status(): return jsonify(spider_status)
