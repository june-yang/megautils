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

"""Raid Adapter"""

import copy

from megautils.raid.mega import Mega
from megautils.raid import str2bool
from megautils import exception
from megautils.raid.virtual_driver import VirtualDriver
from megautils.raid.physical_disk import PhysicalDisk

class Adapter(object):

    def __init__(self, id=None):
        self.id = id

    def __flush__(self):
        if self.id == None:
            raise exception.InvalidParameterValue()

        cmd = '-AdpAllInfo -a%s' % self.id

        ret = self._get_client().command(cmd)
        return self._handle(ret, multi_adapter=False)

    def _get_client(self):
        return Mega()

    def get_adapters(self):
        cmd = '-AdpAllInfo -aALL'

        ret = self._get_client().command(cmd)
        return self._handle(ret)

    def _handle(self, retstr, multi_adapter=True):
        adapters = []
        for line in retstr.readlines():
            if not multi_adapter and len(adapters) > 0:
                return adapters[0]
            if line.startswith('Adapter #'):
                if self.id is not None:
                    adapters.append(self.copy())
                self.id = int(line[9:].strip())
            elif line.startswith('Product Name'):
                offset = line.find(':')
                self.product_name = line[offset + 1:].strip()
            elif line.startswith('Serial No'):
                offset = line.find(':')
                self.serial_number = line[offset + 1:].strip()
            elif line.startswith('FW Package Build'):
                offset = line.find(':')
                self.fw_package_build = line[offset + 1:].strip()
            elif line.startswith('FW Version'):
                offset = line.find(':')
                self.fw_version = line[offset + 1:].strip()
            elif line.startswith('BIOS Version'):
                offset = line.find(':')
                self.bios_version = line[offset + 1:].strip()
            elif line.startswith('WebBIOS Version'):
                offset = line.find(':')
                self.webbios_version = line[offset + 1:].strip()
            elif line.startswith('Preboot CLI Version'):
                offset = line.find(':')
                self.preboot_cli_version = line[offset + 1:].strip()
            elif line.startswith('Boot Block Version'):
                offset = line.find(':')
                self.boot_block_version = line[offset + 1:].strip()
            elif line.startswith('SAS Address'):
                offset = line.find(':')
                self.sas_address = line[offset + 1:].strip()
            elif line.startswith('BBU'):
                offset = line.find(':')
                self.bbu_present = str2bool(line[offset + 1:])
            elif line.startswith('Alarm'):
                offset = line.find(':')
                self.alarm_present = str2bool(line[offset + 1:])
            elif line.startswith('NVRAM'):
                offset = line.find(':')
                self.nvram_present = str2bool(line[offset + 1:])
            elif line.startswith('Serial Debugger'):
                offset = line.find(':')
                self.serial_debugger_present = str2bool(line[offset + 1:])
            elif line.startswith('Flash'):
                offset = line.find(':')
                self.flash_present = str2bool(line[offset + 1:])
            elif line.startswith('Memory Size'):
                offset = line.find(':')
                self.memory_size = line[offset + 1:].strip()
        if self.id is not None:
            adapters.append(self.copy())

        return adapters

    def get_physical_drivers(self):
        """
        get all physical drivers which belongs to zhe adapter
        :return: physical drivers 
        """
        self.__flush__()
        pds = PhysicalDisk(adapter=self.id).get_physical_disks()
        return pds
        

    def get_virtual_drivers(self):
        """
        get all virtual drivers which belongs to zhe adapter
        :return: virtual drivers 
        """
        self.__flush__()
        vds = VirtualDriver(adapter_id=self.id).getall_virtual_drivers()
        return vds

    def copy(self):
        return copy.deepcopy(self)