# calculator.py
#
# Copyright 2024 Vladimir Kosolapov
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

import ipaddress

class IPCalculator:
    def __init__(self):
        self.show_binary = False

    def set_show_binary(self, show_binary):
        self.show_binary = show_binary

    def calculate(self, ip, mask):
        try:
            interface = ipaddress.IPv4Interface(f"{ip}/{mask}")
            network = interface.network
            host_count = network.num_addresses - (2 if mask < 31 else 0)
            results = {
                _('Address'): self.format_ip(interface.ip),
                _('Netmask'): self.format_ip(network.netmask),
                _('Wildcard'): self.format_ip(network.hostmask),
                _('Network'): self.format_ip(network.network_address),
                _('First Host'): self.format_ip(network.network_address + (0 if mask >= 31 else 1)),
                _('Last Host'): self.format_ip(network.broadcast_address - (0 if mask >= 31 else 1)),
                _('Broadcast'): self.format_ip(network.broadcast_address) if mask < 31 else None,
                _('Total Hosts'): f"{host_count}{self.get_host_count_math(mask)}",
                _('PTR Record'): self.get_ptr_record(interface.ip),
                _('Category'): self.get_ip_class(interface.ip)
            }
            return results
        except ValueError:
            return {_('Error'): _('Invalid IP address or mask')}

    def format_ip(self, ip):
        return f"{ip} ({self.ip_to_binary(ip)})" if self.show_binary else str(ip)

    def ip_to_binary(self, ip):
        return '.'.join([bin(int(x)+256)[3:] for x in str(ip).split('.')])

    def get_ip_class(self, ip):
        ip_int = int(ipaddress.IPv4Address(ip))
        ip_ranges = [
            (167772160, 184549375, _('Private (Class A)')),
            (2886729728, 2887778303, _('Private (Class B)')),
            (3232235520, 3232301055, _('Private (Class C)')),
            (2130706432, 2147483647, _('Loopback')),
            (2851995648, 2852061183, _('Link-Local (APIPA)')),
            (3758096384, 4026531839, _('Multicast')),
            (4026531840, 4294967295, _('Reserved')),
        ]

        for start, end, category in ip_ranges:
            if start <= ip_int <= end:
                return category

        return _('Public')

    def int_to_dotted_netmask(self, mask_int):
        mask = (0xffffffff >> (32 - mask_int)) << (32 - mask_int)
        return '.'.join([str((mask >> (8 * i)) & 0xff) for i in range(3, -1, -1)])

    def get_host_count_math(self, mask):
        if mask >= 31:
            return ""
        exponent = 32 - mask
        superscript = ''.join('⁰¹²³⁴⁵⁶⁷⁸⁹'[int(d)] for d in str(exponent))
        return f" (2{superscript} - 2)"

    def get_ptr_record(self, ip):
        reversed_ip = '.'.join(reversed(str(ip).split('.')))
        return f"{reversed_ip}.in-addr.arpa"
