import json
import os
from datetime import datetime
from calendar import timegm
import requests


URL = 'http://localhost:8080/api/v1.3/'
LAST_REPORT_FILE = 'reports.json'

URL_CONFIG = 'http://mongoapi:8000/query/configuration'
CONFIG_FILE = 'config.json'


def get_last_report(name):
    """Get last report time for given name (container or machine)."""
    with open(LAST_REPORT_FILE) as fh:
        j = json.load(fh)
        if name in j:
            last = j[name]
        else:
            last = ''
    return last


def update_reports(tuples):
    """Update report times for (name, time) in the tuple list."""
    with open(LAST_REPORT_FILE) as fh:
        reports = json.load(fh)
    for key, value in tuples:
        reports[key] = value
    with open(LAST_REPORT_FILE, 'w') as fh:
        json.dump(reports, fh)


def nanosecs(ts):
    """Convert timestamp to its equivalent in nanoseconds"""
    whole, decimal = ts.split(".")
    decimal = decimal[:-1]  # Remove final Z
    seconds = timegm(
        datetime.strptime(whole, "%Y-%m-%dT%H:%M:%S").timetuple()
    ) + float("0." + decimal)
    return seconds * 10 ** 9

def get_stats(entry):
    return \
        entry['timestamp'],\
        entry['cpu']['usage']['total'],\
        len(entry['cpu']['usage']['per_cpu_usage']),\
        entry['memory']['usage'],\
        entry['network']['rx_bytes'],\
        entry['network']['tx_bytes']

def get_max_rx():
    with open(CONFIG_FILE, 'r') as f:
            return json.load(f)['scaling']['max_network_rx']

def get_max_tx():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)['scaling']['max_network_tx']

def get_usage(part):
    part_stats = part['stats']
    if len(part_stats) < 2:
        return None
    # Extract relevant data
    time, cpu, num_cores, mem, rx, tx = get_stats(part_stats[-1])
    prev_time, prev_cpu, _, _, prev_rx, prev_tx = get_stats(part_stats[-2])

    # Calculate CPU and memory usage
    if time == prev_time:
        return None

    data_collection_time_interval_ns = nanosecs(time) - nanosecs(prev_time)
    data_collection_time_interval_s = data_collection_time_interval_ns / (10**9)

    cpu_usage = (cpu - prev_cpu) / data_collection_time_interval_ns
    cpu_percent = float(cpu_usage) / float(num_cores) * 100  # Over number of host cores

    mem_percent = float(mem) / float(part['spec']['memory']['limit']) * 100  # Over container's reservation  
  
    network_usage_rx = (rx - prev_rx) / data_collection_time_interval_s * 8
    network_usage_tx = (tx - prev_tx) / data_collection_time_interval_s * 8

    network_percent_rx = (float(network_usage_rx) / get_max_rx()) * 100 #download
    network_percent_tx = (float(network_usage_tx) / get_max_tx()) * 100 #upload

    network_percent = max(network_percent_rx, network_percent_tx)

    return {
        "time": time,
        "cpu": cpu_percent,
        "memory": mem_percent,
        "network": network_percent
    }

def get_machine_usage(hostname):
    try:
        cjson = requests.get(URL + "containers").json()
    except requests.ConnectionError:
        return None

    usage = get_usage(cjson)

    # If this timestamp has been pushed, do not push it again
    if not usage or usage['time'] == get_last_report(hostname):
        return None

    update_reports([(hostname, usage['time'])])
    return [{
        "host": hostname,
        "usage": usage
    }]


def get_container_usage():
    try:
        cjson = requests.get(URL + "docker").json()
    except requests.ConnectionError:
        return None

    usages = []
    updated_reports = []
    for container_id in cjson.keys():
        labels = cjson[container_id]['spec']['labels']
        if 'io.kubernetes.pod.namespace' not in labels or labels['io.kubernetes.pod.namespace'] != 'default':
            continue
        container_id_short = container_id.split('-')[-1].split('.')[0]  # Dependant on the deployment's nomenclature
        usage = get_usage(cjson[container_id])
        # Add usage only if it has not been reported yet
        if usage and usage['time'] != get_last_report(container_id_short):
            usages.append({
                "pod": labels['io.kubernetes.pod.name'],
                "container": container_id_short,
                "usage": usage
            })
            updated_reports.append((container_id_short, usage['time']))

    # If there is no usage, do not report
    if not len(usages):
        return None

    update_reports(updated_reports)
    return usages


def get_hostname():
    with open("hostname") as fh:
        hostname = fh.read().strip()
    return hostname


if __name__ == "__main__":        

    with open(CONFIG_FILE, 'w') as f:
        try:
            cjson = requests.get(URL_CONFIG).json()
            f.write(json.dumps(cjson[0]))
        except requests.ConnectionError:
            exit
            
    host_performance = get_machine_usage(get_hostname())
    if host_performance:
        requests.post("http://mongoapi:8000/performance", data=json.dumps(host_performance))

    container_performance = get_container_usage()
    if container_performance:
        requests.post("http://mongoapi:8000/performance", data=json.dumps(container_performance))
