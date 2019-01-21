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

"""Raid physical disk"""

import copy

from megautils.raid.mega import Mega
from megautils import exception

class PhysicalDisk(object):

    def __init__(self, enclosure=None, slot=None, adapter=None):
        self.adapter = adapter
        self.slot = slot
        self.id = None
        self.enclosure = enclosure
        self.pi_supported = ''
        self.size = 0
        self.manufacturer = ''
        self.model_number = ''
        self.firmware_revision = ''
        self.serial_no = ''
        self.unit_serial_no = ''
        self.guid = ''
        self.protocol = ''
        self.drive_type = ''
        self.firmware_state = 'Online'

    def _get_client(self):
        return Mega()

    def __flush__(self):
        if self.adapter == None:
            raise exception.InvalidParameterValue()

        cmd = '%s LIST' % self.adapter
        ret = self._get_client().command(cmd)
        self._handle(ret, multi_pd=False)

    def get_physical_disks(self):
        cmd = '%s LIST' % self.adapter
        ret = self._get_client().command(cmd)
        return self._handle(ret)

    def _handle(self, retstr, multi_pd=True):
        pds = []
        i = 0
        for line in retstr.readlines():
            if line.startswith('  Enclosure'):
                if not multi_pd and len(pds) > 0:
                    return pds[0]
                if self.id is not None:
                    pds.append(self.copy())
                self.id = i
                i+= 1
                offset = line.find(':')
                self.enclosure = int(line[offset + 1:].strip())
            if line.startswith('  Slot'):
                offset = line.find(':')
                self.slot = int(line[offset + 1:].strip())
            elif line.startswith('  PI Supported'):
                offset = line.find(':')
                self.pi_supported = int(line[offset + 1:].strip())
            elif line.startswith('  SAS Address'):
                offset = line.find(':')
                self.sas_address = line[offset + 1:].strip()
            elif line.startswith('  Size'):
                offset = line.find(':')
                end = line.find('/')
                self.size = int(line[offset + 1:end].strip())
            elif line.startswith('  Manufacturer'):
                offset = line.find(':')
                self.manufacturer = int(line[offset + 1:].strip())
            elif line.startswith('  Model Number'):
                offset = line.find(':')
                self.model_number = int(line[offset + 1:].strip())
            elif line.startswith('  Firmware Revision'):
                offset = line.find(':')
                self.firmware_revision = int(line[offset + 1:].strip())
            elif line.startswith('  Serial No'):
                offset = line.find(':')
                self.serial_no = int(line[offset + 1:].strip())
            elif line.startswith('  Unit Serial No'):
                offset = line.find(':')
                self.unit_serial_no = line[offset + 1:].strip()
            elif line.startswith('  GUID'):
                offset = line.find(':')
                self.guid = line[offset + 1:].strip()
            elif line.startswith('  Protocol'):
                offset = line.find(':')
                self.protocol = line[offset + 1:].strip()
            elif line.startswith('  Drive Type'):
                offset = line.find(':')
                self.drive_type = line[offset + 1:delim].strip()
            if self.id is not None:
                pds.append(self.copy())
            if line.startswith('Device is a Enclosure'):
                break
        return pds

    def copy(self):
        return copy.deepcopy(self)
