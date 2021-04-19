import json
from datetime import datetime, timedelta
import logging

import falcon
import requests
from kubernetes import client, config


logging.basicConfig(level=logging.DEBUG)

config.load_incluster_config()
KUBE_API = client.CoreV1Api()

LOAD_CHECKING_INTERVAL = 3 * 60  # Amount of seconds to go back when averaging load for choosing least busy container
SYSTEM_LOAD_BACKTRACKING_TIME = 5  # Small amount, but enough to make sure we get data of all hosts
JOB_CREATION_THRESHOLD = 80
PERFORMANCE_URL = 'http://mongoapi:8000/query/performance'


def add_dicts(dict1, dict2):
    if dict1.keys() != dict2.keys():
        raise ValueError("Dicts don't have the same keys")
    result = {}
    for key in dict1.keys():
        result[key] = dict1[key] + dict2[key]
    return result


class JsonStreamIterator:
    # Does not accept lists as items, as it only needs to process performance objects
    def __init__(self, response):
        self.ite = response.iter_content(decode_unicode=True)

    def __iter__(self):
        return self

    def __next__(self):
        string = ''
        open_count = 0
        for char in self.ite:
            string += char.decode('utf-8')
            if string[-1] == '{':
                open_count += 1
            if string[-1] == '}':
                open_count -= 1
                if not open_count:
                    break
        if not string:
            raise StopIteration()
        return json.loads(string)


class Test:
    def on_get(self, req, resp):
        return


def get_metric_percentages(pods):
    metrics = {"cpu": 0, "memory": 0, "network": 0}
    labels = pods["labels"]

    total = 0
    no_value = 0
    for metric in metrics:
        if metric in labels:
            metrics[metric], total = int(labels[metric]) / 100
        else:
            no_value += 1

    if total == 1:
        return metric["cpu"], metric["memory"], metric["network"]
    elif total == 0:
        return 1, 1, 1
    else:
        for metric in metrics:
            if metrics[metric] == 0:
                metrics[metric] = (1-total)/no_value
        return metric["cpu"], metric["memory"], metric["network"]

        
class Worker:
    def on_get(self, req, resp):
        pods = req.media

        with open("test.log", 'w') as f:
            f.write(str(pods))

        if not pods:
            resp.status = falcon.HTTP_400
            resp.body = 'Body should contain pod objects'
            return

        container_names = map(lambda pod: pod['container'], pods)
        logging.debug("Querying for pods %s" % " ".join(container_names))
        # Get worker performance
        res = requests.get(PERFORMANCE_URL, data=json.dumps({
            'usage.time': {'$gte': (datetime.utcnow() - timedelta(seconds=LOAD_CHECKING_INTERVAL)).isoformat()},
            'container': {'$in': list(container_names)},
            '$sort': [('usage.time', -1)]
        }))

        logging.debug("Received response %d" % res.status_code)

        # If failed, return first pod
        if res.status_code != 200:
            resp.body = json.dumps(pods[0])
            res.close()
            return

        # Aggregate performances for each container
        performance = {}
        for entry in JsonStreamIterator(res):
            logging.debug(entry)
            container = entry['container']
            if container not in performance:
                performance[container] = {'cpu': 0, 'memory': 0, 'network':0, 'count': 0}
            performance[container]['cpu'] += entry['usage']['cpu']
            performance[container]['memory'] += entry['usage']['memory']
            performance[container]['network'] += entry['usage']['network']
            performance[container]['count'] += 1

        res.close()
        # If there is no data, return first pod
        if not performance:
            resp.body = json.dumps(pods[0])
            return

        # Average CPU and memory load
        for perf in performance.values():
            perf['cpu'] /= perf['count']
            perf['memory'] /= perf['count']
            perf['network'] /= perf['count']
            del perf['count']
        
        cpu_percent, memory_percent, network_percent = get_metric_percentages(pods)
        with open("labels.log", 'w') as f:
            f.write(str(cpu_percent) + str(memory_percent) + str(network_percent))

        cpu_percent, memory_percent, network_percent = 1, 1, 1
        selected_container = min(performance.items(), key=lambda tup: tup[1]['cpu']*cpu_percent + tup[1]['memory']*memory_percent + tup[1]['network']*network_percent / 3)[0]
        resp.body = json.dumps(list(filter(lambda pod: pod['container'] == selected_container, pods))[0])


class SystemLoad:
    def on_get(self, req, resp):
        res = requests.get(PERFORMANCE_URL, data=json.dumps({
            'usage.time': {'$gte': (datetime.utcnow() - timedelta(seconds=SYSTEM_LOAD_BACKTRACKING_TIME)).isoformat()},
            'host': {'$exists': True},
            '$sort': [('usage.time', -1)]
        }))

        can_run_job = True
        if res.status_code != 200:
            res.close()
        else:
            included_hosts = []
            host_usages = []
            # Last usage of each host
            for entry in JsonStreamIterator(res):
                if entry['host'] not in included_hosts:
                    del entry['usage']['time']
                    host_usages.append(entry['usage'])
                    included_hosts.append(entry['host'])

            # Average usages
            from functools import reduce
            accums = reduce(add_dicts, host_usages)
            for value in accums.values():
                if value / len(included_hosts) > JOB_CREATION_THRESHOLD:
                    can_run_job = False

        resp.body = json.dumps({'status': can_run_job})


api = falcon.API()
workerResource = Worker()
systemLoadResource = SystemLoad()
api.add_route('/test', Test())
api.add_route('/worker', workerResource)
api.add_route('/sysload', systemLoadResource)
