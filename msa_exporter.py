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
VOLUME_PROPERTIES_AS_LABEL_MAPPING = {'volume-name': 'volume'}
POOLSTATS_PROPERTIES_AS_LABEL_MAPPING = {'pool': 'pool', 'serial-number': 'serial'}
POOL_PROPERTIES_AS_LABEL_MAPPING = {'name': 'pool', 'serial-number': 'serial'}
TIER_PROPERTIES_AS_LABEL_MAPPING = {'tier': 'tier', 'pool': 'pool', 'serial-number': 'serial'}
CONTROLLER_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'controller'}
PSU_PROPERTIES_AS_LABEL_MAPPING = {'durable-id': 'psu', 'serial-number': 'serial'}


METRICS = {
    'hostport_data_read': {
        'description': 'Data Read',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="data-read-numeric"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_data_written': {
        'description': 'Data Written',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="data-written-numeric"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_avg_resp_time_read': {
        'description': 'Read Response Time',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="avg-read-rsp-time"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_avg_resp_time_write': {
        'description': 'Write Response Time',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="avg-write-rsp-time"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_avg_resp_time': {
        'description': 'I/O Response Time',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="avg-rsp-time"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_queue_depth': {
        'description': 'Queue Depth',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="queue-depth"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_reads': {
        'description': 'Reads',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="number-of-reads"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'hostport_writes': {
        'description': 'Writes',
        'sources': {
            'path': 'host-port-statistics',
            'object_selector': './OBJECT[@name="host-port-statistics"]',
            'property_selector': './PROPERTY[@name="number-of-writes"]',
            'properties_as_label': HOSTPORTSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_temperature': {
        'description': 'Temperature',
        'sources': {
            'path': 'disks',
            'object_selector': "./OBJECT[@name='drive']",
            'property_selector': './PROPERTY[@name="temperature-numeric"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_iops': {
        'description': 'IOPS',
        'sources': {
            'path': 'disk-statistics',
            'object_selector': "./OBJECT[@name='disk-statistics']",
            'property_selector': './PROPERTY[@name="iops"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_bps': {
        'description': 'Bytes per second',
        'sources': {
            'path': 'disks',
            'object_selector': "./OBJECT[@name='disk-statistics']",
            'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_avg_resp_time': {
        'description': 'Average I/O Response Time',
        'sources': {
            'path': 'disks',
            'object_selector': "./OBJECT[@name='drive']",
            'property_selector': './PROPERTY[@name="avg-rsp-time"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_ssd_life_left': {
        'description': 'SSD Life Remaining',
        'sources': {
            'path': 'disks',
            'object_selector': "./OBJECT[@name='drive']/PROPERTY[@name='architecture'][text()='SSD']/..",
            'property_selector': './PROPERTY[@name="ssd-life-left-numeric"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_health': {
        'description': 'Health',
        'sources': {
            'path': 'disks',
            'object_selector': "./OBJECT[@name='drive']",
            'property_selector': './PROPERTY[@name="health-numeric"]',
            'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'disk_errors': {
        'description': 'Errors',
        'sources': [
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="smart-count-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'smart', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="smart-count-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'smart', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="io-timeout-count-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'io-timeout', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="io-timeout-count-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'io-timeout', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="no-response-count-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'no-response', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="no-response-count-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'no-response', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="spinup-retry-count-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'spinup-retry', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="spinup-retry-count-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'spinup-retry', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-media-errors-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'media-errors', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-media-errors-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'media-errors', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-nonmedia-errors-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'nonmedia-errors', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-nonmedia-errors-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'nonmedia-errors', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-block-reassigns-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'block-reassigns', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-block-reassigns-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'block-reassigns', 'port': 2}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-bad-blocks-1"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'bad-blocks', 'port': 1}
            },
            {
                'path': 'disk-statistics',
                'object_selector': "./OBJECT[@name='disk-statistics']",
                'property_selector': './PROPERTY[@name="number-of-bad-blocks-2"]',
                'properties_as_label': DISK_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'type': 'bad-blocks', 'port': 2}
            }
        ]
    },
    'volume_health': {
        'description': 'Health',
        'sources': {
            'path': 'volumes',
            'object_selector': './OBJECT[@name="volume"]',
            'property_selector': './PROPERTY[@name="health-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_iops': {
        'description': 'IOPS',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="iops"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_bps': {
        'description': 'Bytes per second',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_reads': {
        'description': 'Reads',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="number-of-reads"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_writes': {
        'description': 'Writes',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="number-of-writes"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_data_read': {
        'description': 'Data Read',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="data-read-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_data_written': {
        'description': 'Data Written',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="data-written-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_shared_pages': {
        'description': 'Shared Pages',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="shared-pages"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_read_hits': {
        'description': 'Read-Cache Hits',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="read-cache-hits"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_read_misses': {
        'description': 'Read-Cache Misses',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="read-cache-misses"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_write_hits': {
        'description': 'Read-Cache Hits',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-hits"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_write_misses': {
        'description': 'Read-Cache Misses',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-misses"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_small_destage': {
        'description': 'Small Destages',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="small-destages"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_full_stripe_write_destages': {
        'description': 'Full Stripe Write Destages',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="full-stripe-write-destages"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_read_ahead_ops': {
        'description': 'Read-Ahead Operations',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="read-ahead-operations"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_write_cache_space': {
        'description': 'Write Cache Space',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-space"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_write_cache_percent': {
        'description': 'Write Cache Percentage',
        'sources': {
            'path': 'volume-statistics',
            'object_selector': './OBJECT[@name="volume-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-percent"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_size': {
        'description': 'Size',
        'sources': {
            'path': 'volumes',
            'object_selector': './OBJECT[@name="volume"]',
            'property_selector': './PROPERTY[@name="size-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_total_size': {
        'description': 'Total Size',
        'sources': {
            'path': 'volumes',
            'object_selector': './OBJECT[@name="volume"]',
            'property_selector': './PROPERTY[@name="total-size-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_allocated_size': {
        'description': 'Total Size',
        'sources': {
            'path': 'volumes',
            'object_selector': './OBJECT[@name="volume"]',
            'property_selector': './PROPERTY[@name="allocated-size-numeric"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_blocks': {
        'description': 'Blocks',
        'sources': {
            'path': 'volumes',
            'object_selector': './OBJECT[@name="volume"]',
            'property_selector': './PROPERTY[@name="blocks"]',
            'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'volume_tier_distribution': {
        'description': 'Volume tier distribution',
        'sources': [
            {
                'path': 'volume-statistics',
                'object_selector': './OBJECT[@name="volume-statistics"]',
                'property_selector': './PROPERTY[@name="percent-tier-ssd"]',
                'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'tier': 'Performance'}
            },
            {
                'path': 'volume-statistics',
                'object_selector': './OBJECT[@name="volume-statistics"]',
                'property_selector': './PROPERTY[@name="percent-tier-sas"]',
                'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'tier': 'Standard'}
            },
            {
                'path': 'volume-statistics',
                'object_selector': './OBJECT[@name="volume-statistics"]',
                'property_selector': './PROPERTY[@name="percent-tier-sata"]',
                'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'tier': 'Archive'}
            },
            {
                'path': 'volume-statistics',
                'object_selector': './OBJECT[@name="volume-statistics"]',
                'property_selector': './PROPERTY[@name="percent-allocated-rfc"]',
                'properties_as_label': VOLUME_PROPERTIES_AS_LABEL_MAPPING,
                'labels': {'tier': 'RFC'}
            },
        ]
    },
    'pool_data_read': {
        'description': 'Data Read',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './OBJECT[@name="pool-statistics"]',
            'property_selector': './/PROPERTY[@name="data-read-numeric"]',
            'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_data_written': {
        'description': 'Data Written',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './OBJECT[@name="pool-statistics"]',
            'property_selector': './/PROPERTY[@name="data-written-numeric"]',
            'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_avg_resp_time': {
        'description': 'I/O Response Time',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './OBJECT[@name="pool-statistics"]',
            'property_selector': './/PROPERTY[@name="avg-rsp-time"]',
            'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_avg_resp_time_read': {
        'description': 'Read Response Time',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './OBJECT[@name="pool-statistics"]',
            'property_selector': './/PROPERTY[@name="avg-read-rsp-time"]',
            'properties_as_label': POOLSTATS_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_total_size': {
        'description': 'Total Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="total-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_available_size': {
        'description': 'Available Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="total-avail-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_snapshot_size': {
        'description': 'Snapshot Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="snap-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_allocated_pages': {
        'description': 'Allocated Pages',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="allocated-pages"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_available_pages': {
        'description': 'Available Pages',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="available-pages"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_metadata_volume_size': {
        'description': 'Metadata Volume Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="metadata-vol-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_total_rfc_size': {
        'description': 'Total RFC Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="total-rfc-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_available_rfc_size': {
        'description': 'Available RFC Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="available-rfc-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_reserved_size': {
        'description': 'Reserved Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="reserved-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'pool_unallocated_reserved_size': {
        'description': 'Unallocated Reserved Size',
        'sources': {
            'path': 'pools',
            'object_selector': './OBJECT[@name="pools"]',
            'property_selector': './PROPERTY[@name="reserved-unalloc-size-numeric"]',
            'properties_as_label': POOL_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_reads': {
        'description': 'Reads',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="number-of-reads"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_writes': {
        'description': 'Writes',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="number-of-writes"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_data_read': {
        'description': 'Data Read',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="data-read-numeric"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_data_written': {
        'description': 'Data Written',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="data-written-numeric"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_avg_resp_time': {
        'description': 'I/O Response Time',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="avg-rsp-time"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_avg_resp_time_read': {
        'description': 'Read Response Time',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="avg-read-rsp-time"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'tier_avg_resp_time_write': {
        'description': 'Write Response Time',
        'sources': {
            'path': 'pool-statistics',
            'object_selector': './/OBJECT[@name="tier-statistics"]',
            'property_selector': './/PROPERTY[@name="avg-write-rsp-time"]',
            'properties_as_label': TIER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'enclosure_power': {
        'description': 'Power consumption in watts',
        'sources': {
            'path': 'enclosures',
            'object_selector': './OBJECT[@name="enclosures"]',
            'property_selector': './PROPERTY[@name="enclosure-power"]',
            'properties_as_label': {'enclosure-id': 'id', 'enclosure-wwn': 'wwn'}
        }
    },
    'controller_cpu': {
        'description': 'CPU Load',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="cpu-load"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_iops': {
        'description': 'IOPS',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="iops"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_bps': {
        'description': 'Bytes per second',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="bytes-per-second-numeric"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_read_hits': {
        'description': 'Read-Cache Hits',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="read-cache-hits"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_read_misses': {
        'description': 'Read-Cache Misses',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="read-cache-misses"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_write_hits': {
        'description': 'Write-Cache Hits',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-hits"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'controller_write_misses': {
        'description': 'Write-Cache Misses',
        'sources': {
            'path': 'controller-statistics',
            'object_selector': './OBJECT[@name="controller-statistics"]',
            'property_selector': './PROPERTY[@name="write-cache-misses"]',
            'properties_as_label': CONTROLLER_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'psu_health': {
        'description': 'Power-supply unit health',
        'sources': {
            'path': 'enclosure',
            'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
            'property_selector': './PROPERTY[@name="health-numeric"]',
            'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'psu_status': {
        'description': 'Power-supply unit status',
        'sources': {
            'path': 'enclosure',
            'object_selector': './OBJECT[@name="enclosures"]/OBJECT[@name="power-supplies"]',
            'property_selector': './PROPERTY[@name="status-numeric"]',
            'properties_as_label': PSU_PROPERTIES_AS_LABEL_MAPPING
        }
    },
    'system_health': {
        'description': 'System health',
        'sources': {
            'path': 'system',
            'object_selector': './OBJECT[@name="system-information"]',
            'property_selector': './PROPERTY[@name="health-numeric"]',
        }
    },
}


class MetricStore(object):
    def __init__(self):
        self.metrics = {}

    def get_or_create(self, metric_type, name, description, labels):
        metric_key = (name, tuple(labels.keys()))

        if metric_key not in self.metrics:
            if metric_type == 'gauge':
                self.metrics[metric_key] = prometheus_client.Gauge(name, description, tuple(labels.keys()))
            else:
                raise RuntimeError('Unknown metric type "%s"' % metric_type)

        metric = self.metrics[metric_key]

        if labels:
            return metric.labels(**labels)
        else:
            return metric


def scrap_msa(metrics_store, host, login, password):
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
        name = PREFIX + name
        if isinstance(metric['sources'], dict):
            sources = [metric['sources']]
        else:
            sources = metric['sources']

        for source in sources:
            if source['path'] not in path_cache:
                response = session.get('https://%s/api/show/%s' % (host, source['path']))
                response.raise_for_status()
                path_cache[source['path']] = lxml.etree.fromstring(response.content)

            xml = path_cache[source['path']]

            for obj in xml.xpath(source['object_selector']):
                labels = {source['properties_as_label'][elem.get('name')]: elem.text for elem in obj
                          if elem.get('name') in source.get('properties_as_label', {})}
                labels.update(source.get('labels', {}))
                value = obj.find(source['property_selector']).text
                if value == 'N/A' : value = 'nan'
                metrics_store.get_or_create(metric.get('type', 'gauge'), name, metric['description'], labels).set(value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('login')
    parser.add_argument('password')
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('-i', '--interval', type=int, default=60)

    args = parser.parse_args()

    prometheus_client.start_http_server(args.port)
    metrics_store = MetricStore()
    while True:
        scrap_msa(metrics_store, args.hostname, args.login, args.password)
        time.sleep(args.interval)
