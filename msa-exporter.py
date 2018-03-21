#!/usr/bin/env python3

import hashlib
import time
import argparse

import requests
import prometheus_client
import lxml.etree


import xml.etree.ElementTree as ET


PREFIX = 'msa_'
HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'port'}
DISK_PROPERTIES_AS_LABEL_MAPPING = {'location': 'location',
                                    'serial-number': 'serial'}
VOLUME_PROPERTIES_AS_LABEL_MAPPING = {'volume-name': 'name'}
POOLSTATS_PROPERTIES_AS_LABEL_MAPPING = {'pool': 'pool', 'serial-number': 'serial'}
POOL_PROPERTIES_AS_LABEL_MAPPING = {'name': 'pool', 'serial-number': 'serial'}
TIER_PROPERTIES_AS_LABEL_MAPPING = {'tier': 'tier', 'pool': 'pool', 'serial-number': 'serial'}
CONTROLLER_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'controller'}
PSU_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'psu', 'serial-number': 'serial'}


METRICS = {
    'hostport_data_read': {
        'description': 'Data Read',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="data-read-numeric"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_data_written': {
        'description': 'Data Written',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="data-written-numeric"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_avg_resp_time_read': {
        'description': 'Read Response Time',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="avg-read-rsp-time"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_avg_resp_time_write': {
        'description': 'Write Response Time',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="avg-write-rsp-time"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_avg_resp_time': {
        'description': 'I/O Response Time',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="avg-rsp-time"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_queue_depth': {
        'description': 'Queue Depth',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="queue-depth"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_reads': {
        'description': 'Reads',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="number-of-reads"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'hostport_writes': {
        'description': 'Writes',
        'path': 'host-port-statistics',
        'object_selector': './OBJECT[@name="host-port-statistics"]',
        'property_selector': './PROPERTY[@name="number-of-writes"]',
        'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_temperature': {
        'description': 'Temperature',
        'path': 'disks',
        'object_selector': "./OBJECT[@name='drive']",
        'property_selector': './PROPERTY[@name="temperature-numeric"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_iops': {
        'description': 'IOPS',
        'path': 'disk-statistics',
        'object_selector': "./OBJECT[@name='disk-statistics']",
        'property_selector': './PROPERTY[@name="iops"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_bps': {
        'description': 'Bytes per second',
        'path': 'disks',
        'object_selector': "./OBJECT[@name='disk-statistics']",
        'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_avg_resp_time': {
        'description': 'Average I/O Response Time',
        'path': 'disks',
        'object_selector': "./OBJECT[@name='drive']",
        'property_selector': './PROPERTY[@name="avg-rsp-time"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_ssd_life_left': {
        'description': 'SSD Life Remaining',
        'path': 'disks',
        'object_selector': "./OBJECT[@name='drive']/PROPERTY[@name='architecture'][text()='SSD']/..",
        'property_selector': './PROPERTY[@name="ssd-life-left-numeric"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'disk_health': {
        'description': 'Health',
        'path': 'disks',
        'object_selector': "./OBJECT[@name='drive']",
        'property_selector': './PROPERTY[@name="health-numeric"]',
        'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_health': {
        'description': 'Health',
        'path': 'volumes',
        'object_selector': './OBJECT[@name="volume"]',
        'property_selector': './PROPERTY[@name="health-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_iops': {
        'description': 'IOPS',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="iops"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_bps': {
        'description': 'Bytes per second',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_reads': {
        'description': 'Reads',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="number-of-reads"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_writes': {
        'description': 'Writes',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="number-of-writes"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_data_read': {
        'description': 'Data Read',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="data-read-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_data_written': {
        'description': 'Data Written',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="data-written-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_shared_pages': {
        'description': 'Shared Pages',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="shared-pages"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_read_hits': {
        'description': 'Read-Cache Hits',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="read-cache-hits"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_read_misses': {
        'description': 'Read-Cache Misses',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="read-cache-misses"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_write_hits': {
        'description': 'Read-Cache Hits',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-hits"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_write_misses': {
        'description': 'Read-Cache Misses',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-misses"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_small_destage': {
        'description': 'Small Destages',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="small-destages"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_full_stripe_write_destages': {
        'description': 'Full Stripe Write Destages',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="full-stripe-write-destages"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_read_ahead_ops': {
        'description': 'Read-Ahead Operations',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="read-ahead-operations"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_write_cache_space': {
        'description': 'Write Cache Space',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-space"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_write_cache_percent': {
        'description': 'Write Cache Percentage',
        'path': 'volume-statistics',
        'object_selector': './OBJECT[@name="volume-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-percent"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_size': {
        'description': 'Size',
        'path': 'volumes',
        'object_selector': './OBJECT[@name="volume"]',
        'property_selector': './PROPERTY[@name="size-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_total_size': {
        'description': 'Total Size',
        'path': 'volumes',
        'object_selector': './OBJECT[@name="volume"]',
        'property_selector': './PROPERTY[@name="total-size-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_allocated_size': {
        'description': 'Total Size',
        'path': 'volumes',
        'object_selector': './OBJECT[@name="volume"]',
        'property_selector': './PROPERTY[@name="allocated-size-numeric"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'volume_blocks': {
        'description': 'Blocks',
        'path': 'volumes',
        'object_selector': './OBJECT[@name="volume"]',
        'property_selector': './PROPERTY[@name="blocks"]',
        'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_data_read': {
        'description': 'Data Read',
        'path': 'pool-statistics',
        'object_selector': './OBJECT[@name="pool-statistics"]',
        'property_selector': './/PROPERTY[@name="data-read-numeric"]',
        'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_data_written': {
        'description': 'Data Written',
        'path': 'pool-statistics',
        'object_selector': './OBJECT[@name="pool-statistics"]',
        'property_selector': './/PROPERTY[@name="data-written-numeric"]',
        'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_avg_resp_time': {
        'description': 'I/O Response Time',
        'path': 'pool-statistics',
        'object_selector': './OBJECT[@name="pool-statistics"]',
        'property_selector': './/PROPERTY[@name="avg-rsp-time"]',
        'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_avg_resp_time_read': {
        'description': 'Read Response Time',
        'path': 'pool-statistics',
        'object_selector': './OBJECT[@name="pool-statistics"]',
        'property_selector': './/PROPERTY[@name="avg-read-rsp-time"]',
        'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_total_size': {
        'description': 'Total Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="total-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_available_size': {
        'description': 'Available Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="total-avail-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_snapshot_size': {
        'description': 'Snapshot Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="snap-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_allocated_pages': {
        'description': 'Allocated Pages',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="allocated-pages"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_available_pages': {
        'description': 'Available Pages',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="available-pages"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_metadata_volume_size': {
        'description': 'Metadata Volume Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="metadata-vol-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_total_rfc_size': {
        'description': 'Total RFC Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="total-rfc-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_available_rfc_size': {
        'description': 'Available RFC Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="available-rfc-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_reserved_size': {
        'description': 'Reserved Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="reserved-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'pool_unallocated_reserved_size': {
        'description': 'Unallocated Reserved Size',
        'path': 'pools',
        'object_selector': './OBJECT[@name="pools"]',
        'property_selector': './PROPERTY[@name="reserved-unalloc-size-numeric"]',
        'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_reads': {
        'description': 'Reads',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="number-of-reads"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_writes': {
        'description': 'Writes',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="number-of-writes"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_data_read': {
        'description': 'Data Read',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="data-read-numeric"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_data_written': {
        'description': 'Data Written',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="data-written-numeric"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_avg_resp_time': {
        'description': 'I/O Response Time',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="avg-rsp-time"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_avg_resp_time_read': {
        'description': 'Read Response Time',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="avg-read-rsp-time"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'tier_avg_resp_time_write': {
        'description': 'Write Response Time',
        'path': 'pool-statistics',
        'object_selector': './/OBJECT[@name="tier-statistics"]',
        'property_selector': './/PROPERTY[@name="avg-write-rsp-time"]',
        'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
    },
    'enclosure_power': {
        'description': 'Power consumption in watts',
        'path': 'enclosures',
        'object_selector': './OBJECT[@name="enclosures"]',
        'property_selector': './PROPERTY[@name="enclosure-power"]',
        'properties_as_label': {'enclosure-id': 'id', 'enclosure-wwn': 'wwn'}
    },
    'controller_cpu': {
        'description': 'CPU Load',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="cpu-load"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_iops': {
        'description': 'IOPS',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="iops"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_bps': {
        'description': 'Bytes per second',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_read_hits': {
        'description': 'Read-Cache Hits',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="read-cache-hits"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_read_misses': {
        'description': 'Read-Cache Misses',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="read-cache-misses"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_write_hits': {
        'description': 'Write-Cache Hits',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-hits"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'controller_write_misses': {
        'description': 'Write-Cache Misses',
        'path': 'controller-statistics',
        'object_selector': './OBJECT[@name="controller-statistics"]',
        'property_selector': './PROPERTY[@name="write-cache-misses"]',
        'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
    },
    'psu_health': {
        'description': 'Power-supply unit health',
        'path': 'enclosure',
        'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
        'property_selector': './PROPERTY[@name="health-numeric"]',
        'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING
    },
    'psu_status': {
        'description': 'Power-supply unit status',
        'path': 'enclosure',
        'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
        'property_selector': './PROPERTY[@name="status-numeric"]',
        'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING
    },
    'system_health': {
        'description': 'System health',
        'path': 'system',
        'object_selector': './OBJECT[@name="system-information"]',
        'property_selector': './PROPERTY[@name="health-numeric"]',
    },
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
                                                            list(metric.get('labels', [])) + list(metric.get('properties_as_label', {}).values()))
            else:
                continue  # Ignore bad metric types

        xml = path_cache[metric['path']]

        for obj in xml.xpath(metric['object_selector']):
            labels = {metric['properties_as_label'][elem.get('name')]: elem.text for elem in obj
                      if elem.get('name') in metric.get('properties_as_label', {})}
            labels.update(metric.get('labels', {}))
            value = obj.find(metric['property_selector']).text
            if labels:
                metric['_metric'].labels(**labels).set(float(value))
            else:
                metric['_metric'].set(float(value))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('login')
    parser.add_argument('password')

    args = parser.parse_args()

    prometheus_client.start_http_server(8000)
    while True:
        scrap_msa(args.hostname, args.login, args.password)
        time.sleep(30)
