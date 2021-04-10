import json
import requests
import speedtest

CONFIG_URL = 'http://mongoapi:8000/query/configuration'

if __name__ == "__main__":    
    s = speedtest.Speedtest()
    rx = s.download()
    tx = s.upload()
    
    requests.put(CONFIG_URL, data=json.dumps([{}, {"$set": {"scaling.max_network_tx":0, "scaling.max_network_rx":0} }]))