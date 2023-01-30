from confluent_kafka import Consumer
import pymongo
import sys
import time 
import json

try:
    connection = pymongo.MongoClient("mongodb://mongodb:27017/")
    db = connection["prometheusdata"]

except:
    print("Connection doesn't work..")

c = Consumer({
    'bootstrap.servers': sys.argv[1],
    'group.id': 'group2',
    'auto.offset.reset': 'latest' 
})

c.subscribe([sys.argv[2]])

try:
        while True:
            msg = c.poll(1.0) #viene utilizzata dal consumatore per ottenere i messaggi

            if msg is None:
                # No message available within timeout.
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                print("Waiting for message or event/error in poll()")
                time.sleep(2)
                continue
            elif msg.error():
                print('error: {}'.format(msg.error()))
            else:
                record_value = json.loads(msg.value().decode('utf8', 'strict')) 
                record_key = record_value["query"] #tramite il campo 'query', recupero la Query per creare una collezione

                print("Consumed record with key {} and value {}".format(record_key, record_value))
                try:
                    insert = db[record_key].insert_one(record_value)
                except:
                     print("Errore durante l'inserimento...")
except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    c.close()

