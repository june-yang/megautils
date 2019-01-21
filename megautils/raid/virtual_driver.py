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

from megautils.raid import mega
from megautils import exception

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAID_CONFIG_SCHEMA = os.path.join(CURRENT_DIR, "raid_config_schema.json")


class VirtualDriver(object):

    def __init__(self, adapter_id=None, id=None):
        self.adapter = adapter_id
        self.id = id
        self.name = ''
        self.raid_level = ''
        self.size = ''
        self.state = ''
        self.stripe_size = ''
        self.number_of_drives = 0
        self.span_depth = 0
        self.default_cache_policy = ''
        self.current_cache_policy = ''
        self.access_policy = ''
        self.disk_cache_policy = ''
        self.encryption = ''

    def __flush__(self):
        if self.adapter == None or self.id == None:
            raise exception.InvalidParameterValue()

        cmd = '-LdInfo -L%s -a%s' % (self.id, self.adapter)
        ret = self._get_client().command(cmd)
        self._handle(ret, multi_vd=False)
        

    def _get_client(self):
        return mega.Mega()

    def _handle(self, retstr, multi_vd=False):
        vds = []
        for line in retstr:
            if line.startswith('Virtual Drive'):
                if not multi_vd and len(vds) > 0:
                    return vds[0]
                if self.id is not None:
                    vds.append(self.copy())
                delim = line.find('(')
                offset = line.find(':')
                self.id = int(line[offset + 1:delim].strip())
            if line.startswith('Name'):
                offset = line.find(':')
                self.name = line[offset + 1:].strip()
            elif line.startswith('RAID Level'):
                offset = line.find(':')
                self.raid_level = line[offset + 1:].strip()
            elif line.startswith('Size'):
                delim = line.find(' GB')
                offset = line.find(':')
                self.size = line[offset + 1:delim].strip()
            elif line.startswith('State'):
                offset = line.find(':')
                self.state = line[offset + 1:].strip()
            elif line.startswith('Strip Size'):
                delim = line.find(' KB')
                offset = line.find(':')
                self.stripe_size = line[offset + 1:delim].strip()
            elif line.startswith('Number Of Drives'):
                offset = line.find(':')
                self.number_of_drives = int(line[offset + 1:].strip())
            elif line.startswith('Span Depth'):
                offset = line.find(':')
                self.span_depth = int(line[offset + 1:].strip())
            elif line.startswith('Default Cache Policy'):
                offset = line.find(':')
                self.default_cache_policy = line[offset + 1:].strip()
            elif line.startswith('Current Cache Policy'):
                offset = line.find(':')
                self.current_cache_policy = line[offset + 1:].strip()
            elif line.startswith('Current Access Policy'):
                offset = line.find(':')
                self.access_policy = line[offset + 1:].strip()
            elif line.startswith('Disk Cache Policy'):
                offset = line.find(':')
                self.disk_cache_policy = line[offset + 1:].strip()
            elif line.startswith('Encryption'):
                offset = line.find(':')
                self.encryption = line[offset + 1:].strip()
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
        :return: 
        """

        disk_formater = re.compile(r'^[0-9]+:[0-9]+$')
        for disk in disks:
            if not re.match(disk_formater, disk):
                raise exception.InvalidDiskFormater(disk=disk)

        if raid_level in [mega.RAID_0, mega.RAID_1, mega.RAID_5, mega.RAID_6]:
            cmd = '-CfgLdAdd -r%s [%s] -a%s' % \
                  (mega.RAID_LEVEL_INPUT_MAPPING.get(raid_level),
                   ','.join(disks), self.adapter)
        elif raid_level == mega.RAID_10:
            arrays = ''
            for i in range(len(disks) / 2):
                arrays += ' -Array%s[%s,%s]' % (i, disks.pop(0), disks.pop(0))
            cmd = '-CfgSpanAdd -r%s %s Direct RA WB -a%s' % \
                  (mega.RAID_LEVEL_INPUT_MAPPING.get(raid_level),
                   arrays, self.adapter)
        elif raid_level == mega.RAID_50:
            arrays = ''
            for i in range(len(disks) / 3):
                arrays += ' -Array%s[%s,%s,%s]' % \
                          (i, disks.pop(0), disks.pop(0), disks.pop(0))
            cmd = '-CfgSpanAdd -r%s %s Direct RA WB -a%s' % \
                  (mega.RAID_LEVEL_INPUT_MAPPING.get(raid_level),
                   arrays, self.adapter)
        else:
            arrays = ''
            for i in range(len(disks) / 4):
                arrays += ' -Array%s[%s,%s,%s,%s]' % \
                          (i, disks.pop(0), disks.pop(0), disks.pop(0), disks.pop(0))
            cmd = '-CfgSpanAdd -r%s %s Direct RA WB -a%s' %\
                  (mega.RAID_LEVEL_INPUT_MAPPING.get(raid_level), arrays, self.adapter)


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

        cmd = '-CfgLdDel -L%s -Force -a%s' % (self.id, self.adapter)
        self._get_client().command(cmd)
        self.id = None

    def getall_virtual_drivers(self):
        """
        Get all virtual drivers
        :return: 
        """
        if self.adapter == None:
            raise exception.InvalidParameterValue()

        cmd = '-LdInfo -LALL -a%s' % self.adapter
        ret = self._get_client().command(cmd)
        return self._handle(ret, multi_vd=True)

    def set_boot_able(self):
        """
        Set current virtual driver bootable
        :return:
        """
        self.__flush__()

        cmd = '-AdpBootDrive -set -L%s -a%s' % (self.id, self.adapter)
        self._get_client().command(cmd)


def validate_raid_schema(raid_config):
    """Validates the RAID configuration provided.

    This method validates the RAID configuration provided against
    a JSON schema.

    :param raid_config: The RAID configuration to be validated.
    :raises: InvalidInputError, if validation of the input fails.
    """
    raid_schema_fobj = open(RAID_CONFIG_SCHEMA, 'r')
    raid_config_schema = json.load(raid_schema_fobj)
    try:
        jsonschema.validate(raid_config, raid_config_schema)

    except json_schema_exc.ValidationError as e:
        # NOTE: Even though e.message is deprecated in general, it is said
        # in jsonschema documentation to use this still.
        msg = "RAID config validation error: %s" % e.message
        raise exception.InvalidParameterValue(msg)

    for logical_disk in raid_config['logical_disks']:

        # If user has provided 'number_of_physical_disks' or
        # 'physical_disks', validate that they have mentioned at least
        # minimum number of physical disks required for that RAID level.
        raid_level = logical_disk['raid_level']
        min_disks_reqd = mega.RAID_LEVEL_MIN_DISKS[raid_level]

        no_of_disks_specified = None
        if 'number_of_physical_disks' in logical_disk:
            no_of_disks_specified = logical_disk['number_of_physical_disks']
        elif 'physical_disks' in logical_disk:
            no_of_disks_specified = len(logical_disk['physical_disks'])

        if (no_of_disks_specified and
                    no_of_disks_specified < min_disks_reqd):
            msg = ("RAID level %(raid_level)s requires at least %(number)s "
                   "disks." % {'raid_level': raid_level,
                               'number': min_disks_reqd})
            raise exception.InvalidParameterValue(msg)
