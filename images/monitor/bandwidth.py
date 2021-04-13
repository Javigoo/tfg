import json
import requests
import speedtest

CONFIG_URL = 'http://mongoapi:8000/query'

if __name__ == "__main__":    
    s = speedtest.Speedtest()
    rx = s.download()
    tx = s.upload()
    
    requests.put(CONFIG_URL, data=json.dumps({"tx":tx, "rx":rx}))
