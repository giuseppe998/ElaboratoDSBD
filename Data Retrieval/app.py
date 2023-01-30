from flask import Flask, jsonify, request
from pymongo import *

app = Flask(__name__)

connection = MongoClient("mongodb://mongodb:27017/")
db = connection["prometheusdata"]

@app.route('/', methods = ['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return jsonify({'Status': 'Up'})

@app.route('/Metrics/', methods = ['GET'])
def metrics(): 
    return jsonify({'Metrics': db.list_collection_names()})

@app.route('/Metrics/<string:MetricName>/<string:value>/', methods = ['GET']) # value fa riferimento a metadati, parametri (1h, 3h, 12h) e predizione
def parameters(MetricName, value):
    if (request.method == 'GET'):
        coll = db[MetricName].find_one({'query': MetricName}, sort=[( '_id', DESCENDING )])
        if coll == None:
            return jsonify({'Error Message': 'Metric or value not found'})
        return jsonify({'Metric': MetricName, 'value': coll[value]})

if __name__ == '__main__':
    app.run(debug = True, host="0.0.0.0", port=5000)

