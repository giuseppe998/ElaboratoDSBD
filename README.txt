//COMANDI PER ESEGUIRE L'ELABORATO

1) Buildare le varie immagini attraverso il comando:

docker image build -t nome_immagine .

dove nome_immagine sono:

-etl:0.0.1
-datastorage:0.0.1
-dataretrieval:0.0.1
-slamanager:0.0.1


2) Avviare il docker compose attraverso il comando:

docker-compose up -d

Per recuperare i valori relativi alle metriche (da ETL), sarà richiesto un pò di tempo, in quanto verranno recuperati i dati relativi agli ultimi 2 giorni.


3) Verifica presenza e persistenza dei dati relative alle metriche all'interno del container mongodb (versione mongo utilizzata 4.2.16-bionic) attraverso i comandi:

  1. docker exec -it mongodb bash
  2. mongo
  3. use prometheusdata
  4. show tables (per verificare la presenza di tutte le metriche esaminate)
  5. db.getCollection("nome_metrica").find()


4) Avvio microservizio Data Retrieval per mostrare, attraverso REST API i dati generati da ETL e contenuti nel database:

   1. Nel browser scrivere il path "localhost:5000" e verrà mostrata la pagina di home con il messaggio in formato json "Status:Up";
   2. Attraverso il path "localhost:5000/Metrics/", verrà 	mostrata la lista delle metriche disponibili e contenute nel database;
   3. Con il path "localhost:5000/Metrics/nome_metrica/value", verranno mostrati i dati relativi alla data metrica.

dove

'nome_metrica': tra quelle presenti in "localhost:5000/Metrics/"

'value': valori possibili sono 'metadata','parameters_1h', 'parameters_3h', 'parameters_12h', 'prediction'.


5) Avvio microservizio SLA Manager

   1. Nel browser scrivere il path "localhost:5001" e verrà mostrata la pagina di home dove verranno elencate le metriche scelte dello SLA set;

   2. Con il path "localhost:5001/createUpdate/nome_metrica/vincolo/value" è possibile creare o aggiornare il vincolo relativo a una data metrica;

dove:

'nome_metrica': nome della metrica scelta dalle 5 disponibili

'vincolo' : 'min' o 'max'

'value': un valore intero o float


 Verifica memorizzazione o aggiornamento vincoli nel database su Mongo:

	DB: 'SlaManager' --> use SlaManager

	Collection: 'SlaMetric' --> db.getCollection("SlaMetric").find()


   3. Con il path "localhost:5001/SlaState/nome_metrica/vincolo/parameters/value" è possibile verificare lo stato del SLA;

dove:

'nome_metrica': nome della metrica scelta dalle 5 disponibili

'vincolo': 'min' o 'max'

'parameters': 'parameters_1h', 'parameters_3h', 'parameters_12h' 

'value': se 'vincolo' == 'min' -> 'min_1h', 'min_3h', 'min_12h'   
   
         se 'vincolo' == 'max' -> 'max_1h', 'max_3h', 'max_12h'


   4. Con il path "localhost:5001/SlaStatePrediction/nome_metrica/vincolo/prediction/value" è possibile verificare possibili violazioni future;

dove:

'nome_metrica': nome della metrica scelta dalle 5 disponibili

'vincolo': 'min' o 'max'

'prediction': 'prediction'

'value': se 'vincolo' == 'min' -> 'value' == 'min'

	   se 'vincolo' == 'max' -> 'value' == 'max'











 
