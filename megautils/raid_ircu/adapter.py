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

from megautils.raid_ircu.mega import Mega
from megautils import exception
from megautils.raid_ircu.virtual_driver import VirtualDriver
from megautils.raid_ircu.physical_disk import PhysicalDisk

class Adapter(object):

    def __init__(self, id=None):
        self.id = id

    def __flush__(self):
        if self.id == None:
            raise exception.InvalidParameterValue()

        cmd = '%s DISPLAY' % self.id

        ret = self._get_client().command(cmd)
        return self._handle(ret, multi_adapter=False)

    def _get_client(self):
        return Mega()

    def get_adapters(self):
        cmd = 'LIST'

        ret = self._get_client().command(cmd)
        return self._handle(ret)

    def _handle(self, retstr, multi_adapter=True):
        adapters = []
        ready = 2 # display value played under 2 line from Index-key
        for line in retstr.readlines():
            if not multi_adapter and len(adapters) > 0:
                return adapters[0]
            if line.startswith(' Index'):
                ready-= 1
            elif ready == 1:
                ready-= 1
            elif ready == 0 and not line.startswith('SAS3IRU'):
                values = [i for i in line.split(' ') if i]
                if not multi_adapter and values[0] != self.id:
                    continue
                self.id, self.adp_type, self.vender_id, self.device_id, self.pci_address, self.subsysven_id, self.subsysdev_id = valuedds.pop()
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
