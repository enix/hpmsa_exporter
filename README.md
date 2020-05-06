# HP MSA exporter

A prometheus exporter for the HP MSA Storage SAN.

## Usage

    ./msa_exporter.py --port 8000 --interval 60 msa_san_hostname msa_san_username msa_san_password

## Metrics

This exporter exposes the following metrics:

| Name                                  | Description                | Labels                       |
|---------------------------------------|----------------------------|------------------------------|
| msa_hostport_data_read                | Data Read                  | port                         |
| msa_hostport_data_written             | Data Written               | port                         |
| msa_hostport_avg_resp_time_read       | Read Response Time         | port                         |
| msa_hostport_avg_resp_time_write      | Write Response Time        | port                         |
| msa_hostport_avg_resp_time            | I/O Response Time          | port                         |
| msa_hostport_queue_depth              | Queue Depth                | port                         |
| msa_hostport_reads                    | Reads                      | port                         |
| msa_hostport_writes                   | Writes                     | port                         |
| msa_disk_temperature                  | Temperature                | location, serial             |
| msa_disk_iops                         | IOPS                       | location, serial             |
| msa_disk_bps                          | Bytes per second           | location, serial             |
| msa_disk_avg_resp_time                | Average I/O Response Time  | location, serial             |
| msa_disk_ssd_life_left                | SSD Life Remaining         | location, serial             |
| msa_disk_health                       | Health                     | location, serial             |
| msa_disk_errors                       | Errors                     | location, port, serial, type |
| msa_volume_health                     | Health                     | volume                       |
| msa_volume_iops                       | IOPS                       | volume                       |
| msa_volume_bps                        | Bytes per second           | volume                       |
| msa_volume_reads                      | Reads                      | volume                       |
| msa_volume_writes                     | Writes                     | volume                       |
| msa_volume_data_read                  | Data Read                  | volume                       |
| msa_volume_data_written               | Data Written               | volume                       |
| msa_volume_shared_pages               | Shared Pages               | volume                       |
| msa_volume_read_hits                  | Read-Cache Hits            | volume                       |
| msa_volume_read_misses                | Read-Cache Misses          | volume                       |
| msa_volume_write_hits                 | Read-Cache Hits            | volume                       |
| msa_volume_write_misses               | Read-Cache Misses          | volume                       |
| msa_volume_small_destage              | Small Destages             | volume                       |
| msa_volume_full_stripe_write_destages | Full Stripe Write Destages | volume                       |
| msa_volume_read_ahead_ops             | Read-Ahead Operations      | volume                       |
| msa_volume_write_cache_space          | Write Cache Space          | volume                       |
| msa_volume_write_cache_percent        | Write Cache Percentage     | volume                       |
| msa_volume_size                       | Size                       | volume                       |
| msa_volume_total_size                 | Total Size                 | volume                       |
| msa_volume_allocated_size             | Total Size                 | volume                       |
| msa_volume_blocks                     | Blocks                     | volume                       |
| msa_volume_tier_distribution          | Volume tier distribution   | tier, volume                 |
| msa_pool_data_read                    | Data Read                  | serial, pool                 |
| msa_pool_data_written                 | Data Written               | serial, pool                 |
| msa_pool_avg_resp_time                | I/O Response Time          | serial, pool                 |
| msa_pool_avg_resp_time_read           | Read Response Time         | serial, pool                 |
| msa_pool_total_size                   | Total Size                 | serial, pool                 |
| msa_pool_available_size               | Available Size             | serial, pool                 |
| msa_pool_snapshot_size                | Snapshot Size              | serial, pool                 |
| msa_pool_allocated_pages              | Allocated Pages            | serial, pool                 |
| msa_pool_available_pages              | Available Pages            | serial, pool                 |
| msa_pool_metadata_volume_size         | Metadata Volume Size       | serial, pool                 |
| msa_pool_total_rfc_size               | Total RFC Size             | serial, pool                 |
| msa_pool_available_rfc_size           | Available RFC Size         | serial, pool                 |
| msa_pool_reserved_size                | Reserved Size              | serial, pool                 |
| msa_pool_unallocated_reserved_size    | Unallocated Reserved Size  | serial, pool                 |
| msa_tier_reads                        | Reads                      | serial, pool, tier           |
| msa_tier_writes                       | Writes                     | serial, pool, tier           |
| msa_tier_data_read                    | Data Read                  | serial, pool, tier           |
| msa_tier_data_written                 | Data Written               | serial, pool, tier           |
| msa_tier_avg_resp_time                | I/O Response Time          | serial, pool, tier           |
| msa_tier_avg_resp_time_read           | Read Response Time         | serial, pool, tier           |
| msa_tier_avg_resp_time_write          | Write Response Time        | serial, pool, tier           |
| msa_enclosure_power                   | Power consumption in watts | wwn, id                      |
| msa_controller_cpu                    | CPU Load                   | controller                   |
| msa_controller_iops                   | IOPS                       | controller                   |
| msa_controller_bps                    | Bytes per second           | controller                   |
| msa_controller_read_hits              | Read-Cache Hits            | controller                   |
| msa_controller_read_misses            | Read-Cache Misses          | controller                   |
| msa_controller_write_hits             | Write-Cache Hits           | controller                   |
| msa_controller_write_misses           | Write-Cache Misses         | controller                   |
| msa_psu_health                        | Power-supply unit health   | psu, serial                  |
| msa_psu_status                        | Power-supply unit status   | psu, serial                  |
| msa_system_health                     | System health              |                              |

## Compatible hardware

This exporter has been tested on the following hardware:

 - HP MSA 2050/2052 series using 3.5" and 2.5" backplanes with or without external JBODs
 - DELL ME4024 with 2.5" backplanes
 
 It can probably work on :
 - Dothill/Seagate AssuredSan product
 - Lenovo DS S2200 / S3200
