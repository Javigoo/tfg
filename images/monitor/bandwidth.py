import json
import requests
import speedtest
import traceback
import logging

CONFIG_URL = 'http://mongoapi:8000/query'

if __name__ == "__main__":
    try:
        print("OK")
        s = speedtest.Speedtest()
        rx = s.download()
        tx = s.upload()
        
        requests.put(CONFIG_URL, data=json.dumps({"tx":tx, "rx":rx}))
    except Exception as e:
        print("No OK")
        logging.error(traceback.format_exc())

        with open("log", 'w') as f:
            f.write(e)
        

    
