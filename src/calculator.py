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

from ipaddress import IPv4Interface, IPv4Address

class IPCalculator:
    def __init__(self):
        self.show_binary = False
        self.show_hex = False
        self.binary_cache = {}
        self.hex_cache = {}

    def set_show_binary(self, show_binary):
        self.show_binary = show_binary

    def set_show_hex(self, show_hex):
        self.show_hex = show_hex

    def calculate(self, ip, mask):
        try:
            interface = IPv4Interface(f"{ip}/{mask}")
            network = interface.network
            host_count = network.num_addresses - (2 if mask < 31 else 0)
            results = {
                _('Address'): self.format_ip(interface.ip),
                _('Netmask'): self.format_ip(network.netmask),
                _('Wildcard'): self.format_ip(network.hostmask),
                _('Network'): self.format_ip(network.network_address),
                _('Broadcast'): self.format_ip(network.broadcast_address) if mask < 31 else None,
                _('First Host'): self.format_ip(network.network_address + (0 if mask >= 31 else 1)),
                _('Last Host'): self.format_ip(network.broadcast_address - (0 if mask >= 31 else 1)),
                _('Total Hosts'): f"{host_count}{self.get_host_count_math(mask)}",
                _('Category'): self.get_ip_class(interface.ip),
                _('PTR Record'): self.get_ptr_record(interface.ip),
                _('IPv4 Mapped Address'): self.get_ipv4_mapped(interface.ip),
                _('6to4 Prefix'): self.get_6to4_prefix(interface.ip)
            }
            return results
        except ValueError:
            return {_('Error'): _('Invalid IP address or mask')}

    def format_ip(self, ip):
        result = str(ip)
        if self.show_binary:
            if ip not in self.binary_cache:
                self.binary_cache[ip] = self.ip_to_binary(ip)
            result += f"\n<tt>{self.binary_cache[ip]}</tt>"
        if self.show_hex:
            if ip not in self.hex_cache:
                self.hex_cache[ip] = self.ip_to_hex(ip)
            result += f"\n<tt>{self.hex_cache[ip]}</tt>"
        return result

    def ip_to_binary(self, ip):
        return '.'.join(f"{int(octet):08b}" for octet in str(ip).split('.'))

    def ip_to_hex(self, ip):
        return '.'.join(f"{int(octet):02X}" for octet in str(ip).split('.'))

    def get_ip_class(self, ip):
        ip_int = int(IPv4Address(ip))
        ip_ranges = (
            (167772160, 184549375, _('Private (Class A)')),
            (2886729728, 2887778303, _('Private (Class B)')),
            (3232235520, 3232301055, _('Private (Class C)')),
            (2130706432, 2147483647, _('Loopback')),
            (2851995648, 2852061183, _('Link-Local (APIPA)')),
            (3758096384, 4026531839, _('Multicast')),
            (4026531840, 4294967295, _('Reserved'))
        )

        return next((category for start, end, category in ip_ranges if start <= ip_int <= end), _('Public'))

    def int_to_dotted_netmask(self, mask_int):
        mask = (0xffffffff << (32 - mask_int)) & 0xffffffff
        return f"{mask>>24 & 255}.{mask>>16 & 255}.{mask>>8 & 255}.{mask & 255}"

    def get_host_count_math(self, mask):
        if mask >= 31:
            return ""
        exponent = 32 - mask
        superscript = ''.join('⁰¹²³⁴⁵⁶⁷⁸⁹'[int(d)] for d in str(exponent))
        return f" (2{superscript} - 2)"

    def get_ptr_record(self, ip):
        return f"{'.'.join(str(ip).split('.')[::-1])}.in-addr.arpa"

    def get_ipv4_mapped(self, ip):
        hex_parts = [f"{int(octet):02x}" for octet in str(ip).split('.')]
        return f"::ffff:{hex_parts[0]}{hex_parts[1]}.{hex_parts[2]}{hex_parts[3]}"

    def get_6to4_prefix(self, ip):
        hex_parts = [f"{int(octet):02x}" for octet in str(ip).split('.')]
        return f"2002:{hex_parts[0]}{hex_parts[1]}.{hex_parts[2]}{hex_parts[3]}::/48"
