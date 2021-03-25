import speedtest

if __name__ == "__main__":    
    s = speedtest.Speedtest()
    rx = s.download()
    tx = s.upload()

    with open("bandwidth.txt", 'w') as f:
        f.write("rx: "+str(rx)+", tx: "+str(tx)+"\n")

    #db.configuration.update({}, {$set: {"scaling.max_network_tx":0, "scaling.max_network_rx":0} })