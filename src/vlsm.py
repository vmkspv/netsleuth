# vlsm.py
#
# Copyright 2026 Vladimir Kosolapov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ipaddress import IPv4Network
from .calculator import IPCalculator

class VLSMCalculator:
    def __init__(self):
        self.calculator = IPCalculator()

    def calculate(self, ip, mask, subnets):
        try:
            network = IPv4Network(f"{ip}/{mask}", strict=False)
        except ValueError:
            return {_('Error'): _('Invalid IP address or mask')}

        results = []
        address = int(network.network_address)
        for name, hosts in sorted(subnets, key=lambda subnet: subnet[1], reverse=True):
            prefix = self.get_prefix(hosts)
            if prefix < network.prefixlen:
                return {_('Error'): _('Subnets do not fit in the network')}
            subnet = IPv4Network((address, prefix))
            if subnet.broadcast_address > network.broadcast_address:
                return {_('Error'): _('Subnets do not fit in the network')}
            results.append((name, {
                _('Network'): str(subnet),
                _('Netmask'): str(subnet.netmask),
                _('First Host'): str(subnet.network_address + 1),
                _('Last Host'): str(subnet.broadcast_address - 1),
                _('Broadcast'): str(subnet.broadcast_address),
                _('Required Hosts'): str(hosts),
                _('Total Hosts'): f"{subnet.num_addresses - 2}{self.calculator.get_host_count_math(prefix)}"
            }))
            address += subnet.num_addresses
        return results

    def get_prefix(self, hosts):
        return 32 - max((hosts + 1).bit_length(), 2)
