# Copyright 2016 Mellanox Technologies, Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_log import log

from megautils.exception import PhysicalDisksNotFoundError

LOG = log.getLogger(__name__)

RAID_0 = '0'
RAID_1 = '1'
RAID_10 = '1+0'
RAID_5 = '5'
RAID_6 = '6'
RAID_50 = '5+0'
RAID_60 = '6+0'

RAID_LEVEL_MIN_DISKS = {RAID_0: 1,
                        RAID_1: 2,
                        RAID_5: 3,
                        RAID_6: 4,
                        RAID_10: 4,
                        RAID_50: 6,
                        RAID_60: 8}

DISK_TYPE_HDD = 'hdd'
DISK_TYPE_SSD = 'ssd'

DISK_TYPE_MAP = {'SAS': DISK_TYPE_HDD,
                 'SATA': DISK_TYPE_SSD}

def allocate_disks(adapter, virtual_driver_config):
    """
    Allocate physical disks to a virtual driver
    :param adapter: physical disk should be managed with adapter
    :param virtual_driver_config: virtual driver 
    :return: 
    """
    size_gb = 1 if virtual_driver_config['size_gb'] == 'MAX' else virtual_driver_config['size_gb']
    raid_level = virtual_driver_config['raid_level']
    number_of_physical_disks = virtual_driver_config.get(
        'number_of_physical_disks', RAID_LEVEL_MIN_DISKS[raid_level])
    disk_type = virtual_driver_config.get('disk_type', None)
    avail_physical_disks = [x for x in adapter.get_physical_drivers()
                            if 'Online' not in x.state and x.raw_size >= size_gb]

    # hdd and ssd should be split manually cause a raid must stand with same disk type
    avail_ssd_physical_disks = [x for x in avail_physical_disks if _get_disk_type(x.pd_type) == DISK_TYPE_SSD]
    avail_hdd_physical_disks = [x for x in avail_physical_disks if _get_disk_type(x.pd_type) == DISK_TYPE_HDD]

    LOG.info('there are %d ssd and %d hdd available' % (len(avail_ssd_physical_disks), len(avail_hdd_physical_disks)))

    target_physical_disks = None
    if (not disk_type and virtual_driver_config.get('is_root_volume', False))\
            or disk_type == DISK_TYPE_SSD:
        if len(avail_ssd_physical_disks) >= number_of_physical_disks:
            target_physical_disks = avail_ssd_physical_disks
        elif len(avail_ssd_physical_disks) < number_of_physical_disks \
            and disk_type == DISK_TYPE_SSD:
            raise PhysicalDisksNotFoundError()
    elif len(avail_hdd_physical_disks) < number_of_physical_disks:
        if disk_type == DISK_TYPE_HDD:
            raise PhysicalDisksNotFoundError()
        elif len(avail_ssd_physical_disks) < number_of_physical_disks:
            raise PhysicalDisksNotFoundError()
        else:
            target_physical_disks = avail_ssd_physical_disks
    else:
        target_physical_disks = avail_hdd_physical_disks
    if not target_physical_disks:
        raise PhysicalDisksNotFoundError()
    virtual_driver_config['physical_disks'] = ["%s:%s" % (x.enclosure, x.slot)
                                       for x in target_physical_disks][:number_of_physical_disks - 1]


def _get_disk_type(interface):
    return DISK_TYPE_MAP[interface]