from flask import Flask, jsonify, request
from pymongo import *
import yaml

metrics = []

with open('metrics.yaml') as f:
    docs = yaml.load_all(f, Loader=yaml.FullLoader)
    for doc in docs:
        for doc_metric in doc['metrics']:
            metrics.append({'metricName' : doc_metric['metricName'], 'labels' : doc_metric['labels']})

app = Flask(__name__)

connection = MongoClient("mongodb://mongodb:27017/")
db = connection["SlaManager"]
collection = db["SlaMetric"]

db2 = connection["prometheusdata"]

@app.route('/', methods = ['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return jsonify({'Metrics': metrics})

@app.route('/createUpdate/<string:metricName>/<string:constr>/<string:val>/', methods = ['GET'])
def createUpdate(metricName, constr, val): 
    if constr != 'max' and constr != 'min':
        return jsonify({'Error Message': 'Constrain not avaible (constrain avaible min or max)'})
    val = float(val)
    for metric in metrics:
        if  metricName == metric['metricName']:
            coll = collection.find_one({'metricName':metricName, 'constrain':constr})
            if coll != None:
                collection.replace_one(coll, {'metricName':metricName, 'constrain':constr, 'value':val})
                return jsonify({'metricName':metricName, 'constrain':constr, 'value':val, 'Message':'SLO update'})
            else:
                collection.insert_one({'metricName':metricName, 'constrain':constr, 'value':val})
                return jsonify({'metricName':metricName, 'constrain':constr, 'value':val, 'Message':'SLO insert'})
    return jsonify({'Error Message': 'Metric not found'})

@app.route('/SlaState/<string:metricName>/<string:constrain>/<string:parameters>/<string:value>/', methods = ['GET'])
def SlaState(metricName, constrain, parameters, value):
    if constrain != 'max' and constrain != 'min':
        return jsonify({'Error Message': 'Constrain not avaible (constrain avaible min or max)'})
    coll2 = db2[metricName]
    metric = coll2.find_one({'query': metricName}, sort=[( '_id', DESCENDING)])
    if value == 'min_1h' or value == 'min_3h' or value == 'min_12h':
        if constrain == 'min':
            coll = collection.find_one({'constrain': constrain})
            if coll == None:
                return jsonify({'Error Message': 'Constrain not found'})
            elif metric[parameters][value] < coll['value']:
                return jsonify({'SLA State': 'Violated'})
            else:
                return jsonify({'SLA State': 'No Violated'})
        else:
            return jsonify({'Error Message': 'Improper use of parameters'})
    if value == 'max_1h' or value == 'max_3h' or value == 'max_12h':
        if constrain == 'max':
            coll = collection.find_one({'constrain': constrain})
            if coll == None:
                return jsonify({'Error Message': 'Constrain not found'})
            elif metric[parameters][value] > coll['value']:
                return jsonify({'SLA State': 'Violated'})
            else:
                return jsonify({'SLA State': 'No Violated'})
        else:
            return jsonify({'Error Message': 'Improper use of parameters'})

@app.route('/SlaStatePrediction/<string:metricName>/<string:constrain>/<string:prediction>/<string:value>/', methods = ['GET'])
def SlaStatePrediction(metricName, constrain, prediction, value):
    if constrain != 'max' and constrain != 'min':
        return jsonify({'Error Message': 'Constrain not avaible (constrain avaible min or max)'})
    coll2 = db2[metricName]
    metric = coll2.find_one({'query': metricName}, sort=[( '_id', DESCENDING)])
    if value == 'min':
        if constrain == 'min':
            coll = collection.find_one({'constrain': constrain})
            if coll == None:
                return jsonify({'Error Message': 'Constrain not found'})
            elif metric[prediction][value] < coll['value']:
                return jsonify({'SLA State': 'Violated'})
            else:
                return jsonify({'SLA State': 'No Violated'})
        else:
            return jsonify({'Error Message': 'Improper use of parameters'})
    if value == 'max':
        if constrain == 'max':
            coll = collection.find_one({'constrain': constrain})
            if coll == None:
                return jsonify({'Error Message': 'Constrain not found'})
            elif metric[prediction][value] > coll['value']:
                return jsonify({'SLA State': 'Violated'})
            else:
                return jsonify({'SLA State': 'No Violated'})
        else:
            return jsonify({'Error Message': 'Improper use of parameters'})


if __name__ == '__main__':
    app.run(debug = True, host="0.0.0.0", port=5001)