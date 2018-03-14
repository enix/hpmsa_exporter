#!/usr/bin/env python3

import hashlib
import time
import argparse

import requests
import prometheus_client
import lxml.etree


import xml.etree.ElementTree as ET

PREFIX = 'msa_'
DISK_PROPERTIES_AS_LABEL_MAPPING = {'location': 'location',
                                    'serial-number': 'serial'}
VOLUME_PROPERTIES_AS_LABEL_MAPPING = {'volume-name': 'name'}
CONTROLLER_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'controller'}
PSU_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'psu', 'serial-number': 'serial'}

METRICS = {
    'disk_temperature': {'description': 'Temperature',
                         'path': 'disks',
                         'object_selector': "./OBJECT[@name='drive']",
                         'property_name': 'temperature-numeric',
                         'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'disk_iops': {'description': 'IOPS',
                  'path': 'disk-statistics',
                  'object_selector': "./OBJECT[@name='disk-statistics']",
                  'property_name': 'iops',
                  'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'disk_bps': {'description': 'Bytes per second',
                 'path': 'disks',
                 'object_selector': "./OBJECT[@name='disk-statistics']",
                 'property_name': 'bytes-per-second-numeric',
                 'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'disk_avg_resp_time': {'description': 'Average I/O Response Time',
                           'path': 'disks',
                           'object_selector': "./OBJECT[@name='drive']",
                           'property_name': 'avg-rsp-time',
                           'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'disk_ssd_life_left': {'description': 'SSD Life Remaining',
                           'path': 'disks',
                           'object_selector': "./OBJECT[@name='drive']/PROPERTY[@name='architecture'][text()='SSD']/..",
                           'property_name': 'ssd-life-left-numeric',
                           'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'disk_health': {'description': 'Health',
                    'path': 'disks',
                    'object_selector': "./OBJECT[@name='drive']",
                    'property_name': 'health-numeric',
                    'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING},
    'volume_health': {'description': 'Health',
                      'path': 'volumes',
                      'object_selector': './OBJECT[@name="volume"]',
                      'property_name': 'health-numeric',
                      'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING},
    'volume_iops': {'description': 'IOPS',
                    'path': 'volume-statistics',
                    'object_selector': './OBJECT[@name="volume-statistics"]',
                    'property_name': 'iops',
                    'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING},
    'volume_bps': {'description': 'Bytes per second',
                   'path': 'volume-statistics',
                   'object_selector': './OBJECT[@name="volume-statistics"]',
                   'property_name': 'bytes-per-second-numeric',
                   'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING},
    'enclosure_power': {'description': 'Power consumption in watts',
                        'path': 'enclosures',
                        'object_selector': './OBJECT[@name="enclosures"]',
                        'property_name': 'enclosure-power',
                        'properties_as_label': {'enclosure-id': 'id', 'enclosure-wwn': 'wwn'}},
    'controller_cpu': {'description': 'CPU Load',
                       'path': 'controller-statistics',
                       'object_selector': './OBJECT[@name="controller-statistics"]',
                       'property_name': 'cpu-load',
                       'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_iops': {'description': 'IOPS',
                        'path': 'controller-statistics',
                        'object_selector': './OBJECT[@name="controller-statistics"]',
                        'property_name': 'iops',
                        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_bps': {'description': 'Bytes per second',
                       'path': 'controller-statistics',
                       'object_selector': './OBJECT[@name="controller-statistics"]',
                       'property_name': 'bytes-per-second-numeric',
                       'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_read_hits': {'description': 'Read-Cache Hits',
                             'path': 'controller-statistics',
                             'object_selector': './OBJECT[@name="controller-statistics"]',
                             'property_name': 'read-cache-hits',
                             'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_read_misses': {'description': 'Read-Cache Misses',
                               'path': 'controller-statistics',
                               'object_selector': './OBJECT[@name="controller-statistics"]',
                               'property_name': 'read-cache-misses',
                               'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_write_hits': {'description': 'Write-Cache Hits',
                              'path': 'controller-statistics',
                              'object_selector': './OBJECT[@name="controller-statistics"]',
                              'property_name': 'write-cache-hits',
                              'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'controller_write_misses': {'description': 'Write-Cache Misses',
                                'path': 'controller-statistics',
                                'object_selector': './OBJECT[@name="controller-statistics"]',
                                'property_name': 'write-cache-misses',
                                'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING},
    'psu_health': {'description': 'Power-supply unit health',
                   'path': 'enclosure',
                   'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
                   'property_name': 'health-numeric',
                   'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING},
    'psu_status': {'description': 'Power-supply unit status',
                   'path': 'enclosure',
                   'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
                   'property_name': 'status-numeric',
                   'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING},
    'system_health': {'description': 'System health',
                      'path': 'system',
                      'object_selector': './OBJECT[@name="system-information"]',
                      'property_name': 'health-numeric'},
}


def scrap_msa(host, login, password):
    session = requests.Session()
    session.verify = False

    creds = hashlib.md5(b'%s_%s' % (login.encode('utf8'), password.encode('utf8'))).hexdigest()
    response = session.get('https://%s/api/login/%s' % (host, creds))
    response.raise_for_status()
    session_key = ET.fromstring(response.content)[0][2].text

    session.headers['sessionKey'] = session_key
    session.cookies['wbisessionkey'] = session_key
    session.cookies['wbiusername'] = login

    path_cache = {}

    for name, metric in METRICS.items():
        if metric['path'] not in path_cache:
            response = session.get('https://%s/api/show/%s' % (host, metric['path']))
            response.raise_for_status()
            path_cache[metric['path']] = lxml.etree.fromstring(response.content)

        if '_metric' not in metric:
            metric_type = metric.get('type', 'gauge')
            if metric_type == 'gauge':
                metric['_metric'] = prometheus_client.Gauge(PREFIX + name,
                                                            metric['description'],
                                                            ['hostname'] + list(metric.get('properties_as_label', {}).values()))
            else:
                continue  # Ignore bad metric types

        xml = path_cache[metric['path']]

        for obj in xml.xpath(metric['object_selector']):
            labels = {metric['properties_as_label'][elem.get('name')]: elem.text for elem in obj
                      if elem.get('name') in metric.get('properties_as_label', {})}
            labels['hostname'] = host
            value = obj.find("./PROPERTY[@name='%s']" % metric['property_name']).text
            metric['_metric'].labels(**labels).set(float(value))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('login')
    parser.add_argument('password')

    args = parser.parse_args()

    prometheus_client.start_http_server(8000)
    while True:
        scrap_msa(args.hostname, args.login, args.password)
        time.sleep(60)
