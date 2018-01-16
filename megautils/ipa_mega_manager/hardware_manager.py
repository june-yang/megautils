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

from ironic_python_agent import hardware
from megautils.raid.adapter import Adapter
from megautils.raid.virtual_driver import VirtualDriver
from megautils.raid.virtual_driver import validate_raid_schema
from megautils.raid.disk_allocator import allocate_disks

LOG = log.getLogger(__name__)


class MegaHardwareManager(hardware.GenericHardwareManager):
    HARDWARE_MANAGER_VERSION = "4"
    LSI_RAID_PROVIDER = 4

    def evaluate_hardware_support(cls):
        adapters = Adapter().get_adapters()
        return cls.LSI_RAID_PROVIDER if adapters else hardware.HardwareSupport.NONE

    def list_hardware_info(self):
        """Return full hardware inventory as a serializable dict.
        This inventory is sent to Ironic on lookup and to Inspector on
        inspection.
        :return: a dictionary representing inventory
        """
        hardware_info = {}
        hardware_info['interfaces'] = self.list_network_interfaces()
        hardware_info['cpu'] = self.get_cpus()
        hardware_info['disks'] = hardware.list_all_block_devices()
        hardware_info['physical_disks'] = self.list_all_physical_disks()
        hardware_info['memory'] = self.get_memory()
        hardware_info['bmc_address'] = self.get_bmc_address()
        hardware_info['system_vendor'] = self.get_system_vendor_info()
        hardware_info['boot'] = self.get_boot_info()
        return hardware_info

    def list_all_physical_disks(self):
        """
        Get all physical disks to node for allocation
        :return: physical disk dict
        """
        adapters = Adapter().get_adapters()
        cache_physical_drivers = []
        for adapter in adapters:
            pds = adapter.get_physical_drivers()
            for pd in pds:
                cache_physical_drivers.append({
                    'size': pd.raw_size,
                    'type': pd.pd_type,
                    'enclosure': pd.enclosure,
                    'slot': pd.enclosure,
                    'wwn': pd.wwn
                })

        return cache_physical_drivers

    def get_clean_steps(self, node, ports):
        """Return the clean steps supported by this hardware manager.

        This method returns the clean steps that are supported by
        proliant hardware manager.  This method is invoked on every
        hardware manager by Ironic Python Agent to give this information
        back to Ironic.

        :param node: A dictionary of the node object
        :param ports: A list of dictionaries containing information of ports
            for the node
        :returns: A list of dictionaries, each item containing the step name,
            interface and priority for the clean step.
        """
        return [
            {'step': 'create_configuration',
             'interface': 'raid',
             'priority': 0},
            {'step': 'delete_configuration',
             'interface': 'raid',
             'priority': 1}
        ]

    def create_configuration(self, node, ports):
        """
        Create a Raid configuration to the baremetal node
        :param node: ironic node object
        :param ports: ironic port objects
        :return: current raid configuration schema
        """
        LOG.info('creating configuration of node %s' % node['uuid'])

        target_raid_config = node.get('target_raid_config', {}).copy()

        LOG.debug('node raid config: %s' % target_raid_config)
        validate_raid_schema(target_raid_config)

        target_sorted_virtual_driver = (
            sorted((x for x in target_raid_config['logical_disks']
                    if x['size_gb'] != 'MAX'),
                   reverse=True,
                   key=lambda x: x['size_gb']) +
            [x for x in target_raid_config['logical_disks']
             if x['size_gb'] == 'MAX'])

        for target_virtual_driver in target_sorted_virtual_driver:
            adapter = target_virtual_driver.get('controller', 0)
            vd = VirtualDriver(adapter_id=adapter)
            if 'physical_disks' not in target_virtual_driver:
                allocate_disks(adapter, target_virtual_driver)
            count = target_virtual_driver.get('count', 1)
            for i in range(1, count):
                vd.create(target_virtual_driver['raid_level'],
                          target_virtual_driver['physical_disks'])
            if target_raid_config.get('is_root_volume', False)\
                    and count == 1:
                vd.set_boot_able()

        return target_raid_config

    def delete_configuration(self, node, ports):
        """
        Delete all Raid configuration to the baremetal node
        :param node: ironic node object
        :param ports: ironic port objects
        :return: execute messages
        """
        adapters = Adapter().get_adapters()
        cache_virtual_drivers = []
        for adapter in adapters:
            cache_virtual_drivers += adapter.get_virtual_drivers()

        LOG.info('deleting virtual drivers')
        for virtual_driver in cache_virtual_drivers:
            LOG.debug('deleting virtual driver %s of adapter %s' %
                      (virtual_driver.id, virtual_driver.adapter))
            virtual_driver.destroy()
        return 'raid clean execution success'