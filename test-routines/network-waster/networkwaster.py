import json
import os
import logging
import random
import time
import socket
import requests

CONTAINER_NAME = 'monitor-456bk'

OVERLOAD = 60
PERFORMANCE_URL = 'http://mongoapi:8000/query/performance'
CONFIGURATION_URL = 'http://mongoapi:8000/query/configuration'
logging.basicConfig(level=logging.WARNING, format='PID %(process)d - %(levelname)s: %(message)s')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bytes = random._urandom(1490)

def reduce_network_bandwidth():
    res = requests.get(CONFIGURATION_URL)
    a = res.json()[0]['scaling']
    rx = a["max_network_rx"]
    tx = a["max_network_tx"]
    print("before: ", rx, tx)

    #reduce
    requests.put("http://mongoapi:8000/query", data=json.dumps({"tx":tx/2, "rx":rx/2}))

    res = requests.get(CONFIGURATION_URL)
    a = res.json()[0]['scaling']
    rx = a["max_network_rx"]
    tx = a["max_network_tx"]
    print("after: ", rx, tx)

done = False
while not done:
    try:
        res = requests.get(
            PERFORMANCE_URL,
            data=json.dumps({
                'pod': {'$regex': CONTAINER_NAME},
                '$sort': [['usage.time', -1]],
                '$limit': 1,
                'stream': 0
            })
        )
    except:
        print("Error making request")
        logging.info("Error making request")
        time.sleep(1)
        continue
    if res.status_code != 200:
        print('Received code %d' % res.status_code)
        logging.info('Received code %d' % res.status_code)
        time.sleep(1)
        continue
    measurement = res.json()[0]['usage']
    print(measurement)
    if max(measurement['cpu'], measurement['memory'], measurement['network']) > OVERLOAD:
        print('Overload achieved')
        logging.info('Overload achieved')
        done = True
    else:
        print('Reducing network bandwidth')
        logging.info('Reducing network bandwidth')
        reduce_network_bandwidth()
        time.sleep(10)

time.sleep(60)
print("Finished successfully")
logging.info("Finished successfully")
