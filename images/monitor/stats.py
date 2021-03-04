import json
import os
from datetime import datetime
from calendar import timegm
import requests


URL = 'http://localhost:8080/api/v1.3/'
LAST_REPORT_FILE = 'reports.json'

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

def secs(ts):
    """Convert timestamp to its equivalent in seconds"""
    whole, decimal = ts.split(".")
    decimal = decimal[:-1]  # Remove final Z
    seconds = timegm(
        datetime.strptime(whole, "%Y-%m-%dT%H:%M:%S").timetuple()
    ) + float("0." + decimal)
    return seconds


def get_stats(entry):
    return \
        entry['timestamp'],\
        entry['cpu']['usage']['total'],\
        len(entry['cpu']['usage']['per_cpu_usage']),\
        entry['memory']['usage'],\
        entry['network']['rx_bytes'],\
        entry['network']['tx_bytes'],\
        entry['network']['name']


def get_network_percent(rx, tx, prev_rx, prev_tx, network_device, time, prev_time):
    try:
        cjson = requests.get(URL + "machine").json()
        for device in cjson['network_devices']:
            if device['name'] == network_device:
                speed = device['speed']
            
        network_percent = float((max(rx - prev_rx, tx - prev_tx) / (secs(time) - secs(prev_time)) ) * 8) / float(speed * (10**6)) * 100

        return network_percent

    except requests.ConnectionError:
        return None


def get_usage(part):
    part_stats = part['stats']
    if len(part_stats) < 2:
        return None
    # Extract relevant data
    time, cpu, num_cores, mem, rx, tx, network_device = get_stats(part_stats[-1])
    prev_time, prev_cpu, _, _, prev_rx, prev_tx, _ = get_stats(part_stats[-2])

    # Calculate CPU and memory usage
    if time == prev_time:
        return None

    cpu_usage = (cpu - prev_cpu) / (nanosecs(time) - nanosecs(prev_time))
    cpu_percent = float(cpu_usage) / float(num_cores) * 100  # Over number of host cores
    mem_percent = float(mem) / float(part['spec']['memory']['limit']) * 100  # Over container's reservation    
    network_percent = get_network_percent(rx, tx, prev_rx, prev_tx, network_device, time, prev_time) # Over network device speed

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
    host_performance = get_machine_usage(get_hostname())
    if host_performance:
        requests.post("http://mongoapi:8000/performance", data=json.dumps(host_performance))

    container_performance = get_container_usage()
    if container_performance:
        requests.post("http://mongoapi:8000/performance", data=json.dumps(container_performance))
