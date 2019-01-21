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

"""Raid virtual driver"""

import copy
import re
import os
import json
import jsonschema
from jsonschema import exceptions as json_schema_exc

from megautils.raid_ircu import mega
from megautils import exception

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAID_CONFIG_SCHEMA = os.path.join(CURRENT_DIR, "raid_config_schema.json")


class VirtualDriver(object):

    def __init__(self, adapter_id=None, id=None):
        self.adapter = adapter_id
        self.id = id
        self.volume_id = ''
        self.pi_supported = ''
        self.status_of_volume = ''
        self.volume_wwid = ''
        self.raid_level = ''
        self.size = ''
        self.physical_hard_disks = None

    def __flush__(self):
        if self.adapter == None or self.id == None:
            raise exception.InvalidParameterValue()

        cmd = '%s LIST| grep -w 1000 "IR volume %s"' % (self.adapter, self.id)
        ret = self._get_client().command(cmd)
        self._handle(ret, multi_vd=False)

    def _get_client(self):
        return mega.Mega()

    def _handle(self, retstr, multi_vd=True):
        vds = []
        for line in retstr:
            if line.startswith('IR volume'):
                if not multi_vd and len(vds) > 0:
                    return vds[0]
                offset = line.split(' ')
                self.id = int(offset[-1])
                if self.id is not None and multi_vd:
                    vds.append(self.copy())
                offset = line.split(' ')
                self.id = int(offset[-1])
            if line.startswith('  Volume ID'):
                offset = line.find(':')
                self.volume_id = int(line[offset + 1:].strip())
            elif line.startswith('  PI Supported'):
                offset = line.find(':')
                self.pi_supported = line[offset + 1:].strip()
            elif line.startswith('  Status of volume'):
                offset = line.find(':')
                self.status_of_volume = line[offset + 1:].strip()
            elif line.startswith('  Volume wwid'):
                offset = line.find(':')
                self.volume_wwid = line[offset + 1:].strip()
            elif line.startswith('  RAID level'):
                offset = line.find(':')
                self.raid_level = line[offset + 1:delim].strip()
            elif line.startswith('  Size'):
                offset = line.find(':')
                self.size = int(line[offset + 1:].strip())
            elif line.startswith('  Physical hard disks'):
                offset = line.find(':')
                if not self.physical_hard_disks:
                    self.physical_hard_disks = []
            elif line.startswith('  PHY'):
                offset = line.find(':')
                self.physical_hard_disks.append(line[offset + 1:].strip())
            if self.id is not None:
                vds.append(self.copy())

        return vds

    def copy(self):
        return copy.deepcopy(self)

    def create(self, raid_level, disks):
        """
        Create a virtual driver with disks
        :param raid_level: raid level
        :param disks: lsi mega raid create disk schema
        """

        disk_formater = re.compile(r'^[0-9]+:[0-9]+$')
        for disk in disks:
            if not re.match(disk_formater, disk):
                raise exception.InvalidDiskFormater(disk=disk)

        if raid_level in [mega.RAID_0, mega.RAID_1, mega.mega.RAID_10]:
            cmd = '%s CREATE %s MAX %s' % \
                  (self.adapter, mega.RAID_LEVEL_INPUT_MAPPING.get(raid_level),
                   ' '.join(disks))

        ret = self._get_client().command(cmd)
        self.id = None
        for line in ret.readlines():
            offset = line.find('Created VD')
            if offset < 0:
                continue
            self.id = line[offset + 11:]
            break
        if not self.id:
            raise exception.MegaCLIError()
        self.__flush__()

    def destroy(self):
        """
        Delete this raid
        :return:
        """
        self.__flush__()

        cmd = '%s DELETEVOLUME %s' % (self.adapter, self.volume_id)
        self._get_client().command(cmd)
        self.id = None

    def getall_virtual_drivers(self):
        """
        Get all virtual drivers
        :return:
        """
        if self.adapter == None:
            raise exception.InvalidParameterValue()

        cmd = '%s LIST' % self.adapter
        ret = self._get_client().command(cmd)
        return self._handle(ret, multi_vd=True)

    def set_boot_able(self):
        """
        Set current virtual driver bootable
        :return:
        """
        self.__flush__()

        cmd = '%s BOOTIR %s' % (self.adapter, self.volume_id)
        self._get_client().command(cmd)

