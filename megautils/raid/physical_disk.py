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
        self.id = 0
        self.enclosure = enclosure
        self.sequence_number = 0
        self.media_errors = 0
        self.other_errors = 0
        self.predictive_failures = 0
        self.last_predictive_seq_number = 0
        self.pd_type = ''
        self.raw_size = ''
        self.non_coerced_size = ''
        self.wwn = ''
        self.coerced_size = ''
        self.firmware_state = ''
        self.sas_address = ''
        self.connected_port_number = ''
        self.inquiry_data = ''
        self.fde_capable = ''
        self.fde_enable = ''
        self.secured = ''
        self.locked = ''
        self.foreign_state = ''
        self.device_speed = ''
        self.link_speed = ''
        self.media_type = ''

    def _get_client(self):
        return Mega()

    def __flush__(self):
        if not self.enclosure or not self.slot or not self.adapter:
            raise exception.InvalidParameterValue()
        
        cmd = '-PdInfo -PhysDrv [%s:%s] -a%s' % (self.enclosure, self.slot, self.adapter)
        ret = self._get_client().command(cmd)
        self._handle(ret, multi_pd=True)

    def get_physical_disks(self):

        if not self.adapter:
            cmd = '-PdList -aALL'
        elif self.enclosure and self.slot:
            cmd = '-PdInfo -PhysDrv [%s:%s] -a%s' % (self.enclosure, self.slot, self.adapter)
        else:
            cmd = '-PdList -a%s' % self.adapter

        ret = self._get_client().command(cmd)
        return self._handle(ret)
            

    def _handle(self, retstr, multi_pd=True):
        pds = []
        for line in retstr.readlines:
            if line.startswith('Enclosure Device ID'):
                if not multi_pd and len(pds) > 0:
                    return pds[0]
                offset = line.find(':')
                self.enclosure = int(line[offset + 1:].strip())
            if line.startswith('Slot Number'):
                offset = line.find(':')
                self.slot = int(line[offset + 1:].strip())
            elif line.startswith('Device Id'):
                offset = line.find(':')
                self.id = int(line[offset + 1:].strip())
            elif line.startswith('WWN'):
                offset = line.find(':')
                self.wwn = line[offset + 1:].strip()
            elif line.startswith('Sequence Number'):
                offset = line.find(':')
                self.sequence_number = int(line[offset + 1:].strip())
            elif line.startswith('Media Error Count'):
                offset = line.find(':')
                self.media_errors = int(line[offset + 1:].strip())
            elif line.startswith('Other Error Count'):
                offset = line.find(':')
                self.other_errors = int(line[offset + 1:].strip())
            elif line.startswith('Predictive Failure Count'):
                offset = line.find(':')
                self.predictive_failures = int(line[offset + 1:].strip())
            elif line.startswith('Last Predictive Failure Event Seq Number'):
                offset = line.find(':')
                self.last_predictive_seq_number = int(line[offset + 1:].strip())
            elif line.startswith('PD Type'):
                offset = line.find(':')
                self.pd_type = line[offset + 1:].strip()
            elif line.startswith('Raw Size'):
                offset = line.find(':')
                delim = line.find('[') - 4
                self.raw_size = float(line[offset + 1:delim].strip())
            elif line.startswith('Non Coerced Size'):
                offset = line.find(':')
                delim = line.find('[') - 4
                self.non_coerced_size = float(line[offset + 1:delim].strip())
            elif line.startswith('Coerced Size'):
                offset = line.find(':')
                delim = line.find('[') - 4
                self.coerced_size = float(line[offset + 1:delim].strip())
            elif line.startswith('Firmware state'):
                offset = line.find(':')
                self.firmware_state = line[offset + 1:].strip()
            elif line.startswith('SAS Address'):
                offset = line.find(':')
                self.sas_address = line[offset + 1:].strip()
            elif line.startswith('Connected Port Number'):
                offset = line.find(':')
                self.connected_port_number = line[offset + 1:].strip()
            elif line.startswith('Inquiry Data'):
                offset = line.find(':')
                self.inquiry_data = line[offset + 1:].strip()
            elif line.startswith('FDE Capable'):
                offset = line.find(':')
                self.fde_capable = line[offset + 1:].strip()
            elif line.startswith('FDE Enable'):
                offset = line.find(':')
                self.fde_enable = line[offset + 1:].strip()
            elif line.startswith('Secured'):
                offset = line.find(':')
                self.secured = line[offset + 1:].strip()
            elif line.startswith('Locked'):
                offset = line.find(':')
                self.locked = line[offset + 1:].strip()
            elif line.startswith('Foreign State'):
                offset = line.find(':')
                self.foreign_state = line[offset + 1:].strip()
            elif line.startswith('Device Speed'):
                offset = line.find(':')
                self.device_speed = line[offset + 1:].strip()
            elif line.startswith('Link Speed'):
                offset = line.find(':')
                self.link_speed = line[offset + 1:].strip()
            elif line.startswith('Media Type'):
                offset = line.find(':')
                self.media_type = line[offset + 1:].strip()

            pds.append(copy.deepcopy(self))
        return pds

    def copy(self):
        return copy.deepcopy(self)