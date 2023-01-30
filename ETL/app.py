from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame
from prometheus_api_client.utils import parse_datetime
from datetime import timedelta
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf, adfuller
from numpy import std
import warnings
from statsmodels.tsa.ar_model import AutoReg
from sklearn.metrics import mean_squared_error
from time import time,sleep
from datetime import datetime
from requests.exceptions import ConnectTimeout
from confluent_kafka import Producer
import sys
import os
import yaml
import json

if len(sys.argv) != 3:
    sys.stderr.write('Usage: %s <bootstrap-brokers> <topic>\n' % sys.argv[0])
    sys.exit(1)

broker = sys.argv[1]
topic = sys.argv[2]

conf = {'bootstrap.servers': broker}

p = Producer(**conf)

def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d] @ %d\n' % (msg.topic(), msg.partition(), msg.offset()))

time_stamp = time()
date_time = datetime.fromtimestamp(time_stamp)
str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")

os.system('echo ETL container started at ' + str_date_time )
p.produce(topic, 'ETL container started at ' + str_date_time, callback=delivery_callback)
p.flush()

metrics = []

with open('metrics.yaml') as f:
    docs = yaml.load_all(f, Loader=yaml.FullLoader)
    for doc in docs:
        for doc_metric in doc['metrics']:
            metrics.append({'metricName' : doc_metric['metricName'], 'labels' : doc_metric['labels']})

while True:

    time_stamp = time() 

    for metric in metrics:
        init = time()
        try:
            prom = PrometheusConnect(url="http://15.160.61.227:29090", disable_ssl=True)
            start_time = parse_datetime("2d")
            end_time = parse_datetime("now")
            chunk_size = timedelta(minutes=1)
            label_config = metric['labels']

            queryResult = prom.get_metric_range_data(
                metric_name=metric['metricName'],
                label_config=label_config,
                start_time=start_time,
                end_time=end_time,
                chunk_size=chunk_size
            )    
        except ConnectTimeout:
            date_time = datetime.fromtimestamp(time_stamp)
            str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
            os.system('echo ConnectTimeout at : '+ str_date_time +'  retry to connect with prometheus server at : ' + "http://15.160.61.227:29090")
            continue

        qTime = time() - init #tempo necessario per effettuare la query
        print('queryTime:', qTime)
        df = MetricRangeDataFrame(queryResult) 

        init = time()

        #funzione di autocorrelazione
        def Autocorrelation():
            return acf(df.get('value')).tolist()

        autoCorr = Autocorrelation()
        print(autoCorr)

        #stazionarieta' (p_value)
        def Stationariety():
            result_s = adfuller(df.get('value'),autolag='AIC')
            if result_s[1] <= 0.05:
                return True #stazionarietà, non c'è stagionalità
            else:
                return False  #non stazionario, potrebbe esserci stagionalità
        
        stationariety = Stationariety()
        print('Stationarity:', stationariety)

        mTime = time() - init # tempo necessario per recuperare i metadati
        #print('metaTime:', mTime)

        #max, min, avg, dev_std
        numVal = df.shape[0]
        df1 = df[int(numVal-60):] #60: numero di campioni per 1h 
        df3 = df[int(numVal-3*60):] #3*60: numero di campioni per 3h
        df12 = df[int(numVal-12*60):] #12*60: numero di campioni per 12h

        #stagionalita'
        def Seasonality():  
            period = numVal/2 #considero il periodo pari a meta' campioni
            for i in range (0,9): #provo i periodi 10 volte levando il 10% ogni iterazione
                result = seasonal_decompose(df.get('value'), model='add', period= int(period))
                acf_error = acf(result.resid.dropna()) 
                if i == 0: 
                    minAverage = abs(acf_error[1:].mean())
                    minPeriod = period      #calcolo la media dell'autocorrelazione sull'errore. Se sono alla prima iterazione, lo setto come minimo iniziale (alla fine scelgo quello con la media sull'autocorrelazione minore)
                elif acf_error.mean()  < minAverage:  
                    minAverage = abs(acf_error[1:].mean()) 
                    minPeriod = period #tengo conto del periodo in cui ho calcolato la media più bassa
                for j in range(0,len(acf_error) -1): #scorro tutti i campioni di acf e verifico se si ha un comportamento statistico simil white noise
                    if not (acf_error[0] == 1 and abs(acf_error[j]) <= 0.01):
                        period = period - period/10 
                        break
                else: 
                     return {'Seasonality' : True,'Period': int(period)}
            else:     
                result = seasonal_decompose(df.get('value'), model='add', period= int(minPeriod))
                return {'Seasonality' : False, 'Period': int(minPeriod)}

        seasonality = Seasonality()
        print('Seasonality:', seasonality)

        init = time()
        
        def param1h():
            if numVal < 60: #se il numero di campioni e' minore di 60 restituisce null
                return None
            return {'max_1h':df1.max().get('value'),'min_1h':df1.min().get('value'),'avg_1h':df1.get('value').mean(),'dev_std_1h':std(df1.get('value'))}
        
        par1h = param1h()
        print('parameter1h', par1h)
        time1h = time() - init # tempo necessario per recuperare max, min, avg e dev_std dopo 1h
        print('parameter1h:', time1h)

        init = time()

        def param3h():
            if numVal < 180: #3*60: se il numero di campioni e' minore di 180 restituisce null
                return None
            return {'max_3h':df3.max().get('value'),'min_3h':df3.min().get('value'),'avg_3h':df3.get('value').mean(),'dev_std_3h':std(df3.get('value'))}
        
        par3h = param3h()
        print('parameter3h:', par3h)
        time3h = time() - init # tempo necessario per recuperare max, min, avg e dev_std dopo 3h
        print('parameter3h:', time3h)

        init = time()
        
        def param12h():
            if numVal < 720: #12*60: se il numero di campioni e' minore di 720 restituisce null
                return None
            return {'max_12h':df12.max().get('value'),'min_12h':df12.min().get('value'),'avg_12h':df12.get('value').mean(),'dev_std_12h':std(df12.get('value'))}
        
        par12h = param12h()
        print('parameter12h:', par12h)
        time12h = time() - init # tempo necessario per recuperare max, min, avg e dev_std dopo 12h
        print('parameter12h:', time12h)

        #Predizione
        init = time()
        #print(init)

        def pred():
            d = df.xs('value', axis=1)
            result = seasonal_decompose(d, model='add', period=seasonality['Period'])
            data = result.trend.dropna() #droppa i valori mancanti, pulisce i dati
            perc = int(data.shape[0]/10) #prendo il 10% dei valori
            train_data = data.iloc[:-perc] #considero il 90% per la fase di training
            test_data = data.iloc[-perc:] #considero il 10% per la fase di training
            warnings.filterwarnings("ignore")

            predictions = list()
            for i in range (1,10):
                model = AutoReg(train_data, lags = i)
                AR1fit = model.fit()
                start = len(train_data) 
                end = start + len(test_data) - 1
                predictions.append(AR1fit.predict(start=start, end=end))

            errors = list()
            for i in range(0,9):
                errors.append(mean_squared_error(test_data, predictions[i]))
                        
            min = errors[0]
            minindex = 0
            for i in range(0,8):
                if errors[i+1] < min:
                    min = errors[i+1]
                    minindex = i
                        
            model = AutoReg(data, lags = minindex+1)
            ARfit = model.fit()

            fcast = ARfit.predict(start=len(data), end=len(data)+perc, dynamic=False).rename('Forecast')

            return {'average': fcast.mean(),'min': fcast.min(),'max': fcast.max()}

        prediction = pred()
        print(prediction)

        predTime = time() - init # tempo necessario per effettuare la predizione
        print('predictionTime:',predTime)

        date_time = datetime.fromtimestamp(time_stamp)
        str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
        logData = {'time_stamp': str_date_time, 'metric_name': metric['metricName'], 'stats': {'queryTime': qTime, 'metaTime': mTime, 'computationTime1h': time1h,
                'computationTime3h': time3h, 'computationTime12h': time12h, 'predictionTime': predTime}}
        os.system('echo '+ str(logData))

        p.produce(topic, json.dumps({'time_stamp': str_date_time, 'query': metric['metricName'], 'metadata': {'stationarity': stationariety, 
                  'acf': autoCorr, 'seasonality': seasonality['Seasonality']}, 'parameters_1h': par1h, 'parameters_3h': par3h, 'parameters_12h': par12h, 'prediction': prediction}), callback=delivery_callback)
        
        p.poll(0)

    p.flush()

    sleepTime = timedelta(minutes=1).seconds - (time() - time_stamp)
    if sleepTime > 0:
        sleep(sleepTime)








                                            
