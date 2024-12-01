# cmdline.py
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

import sys
import argparse
from ipaddress import AddressValueError, IPv4Address
from .calculator import IPCalculator

class CommandLineInterface:
    def __init__(self, version):
        self.version = version
        self.parser = self.create_argument_parser()
        self.calculator = IPCalculator()

    def create_argument_parser(self):
        parser = TranslatedArgumentParser(
            description=_('A simple utility for the calculation and analysis of IP subnet values, designed to simplify network configuration tasks.')
        )
        parser.add_argument(
            'ip_address',
            type=self.validate_ip,
            nargs='?',
            help=_('ip for calculation')
        )
        parser.options_group.add_argument(
            '-m', '--mask',
            type=self.validate_mask,
            default=24,
            help=_('subnet mask (default: 24)')
        )
        parser.options_group.add_argument(
            '--binary',
            action='store_true',
            help=_('show binary values')
        )
        parser.options_group.add_argument(
            '--hex',
            action='store_true',
            help=_('show hexadecimal values')
        )
        parser.general_group.add_argument(
            '-h', '--help',
            action='help',
            default=argparse.SUPPRESS,
            help=_('show this help message and exit')
        )
        parser.general_group.add_argument(
            '-v', '--version',
            action='store_true',
            help=_('show version information and exit')
        )
        return parser

    def validate_ip(self, value):
        try:
            IPv4Address(value)
            return value
        except (AddressValueError, ValueError):
            raise argparse.ArgumentTypeError('')

    def validate_mask(self, value):
        try:
            mask = int(value)
            if 0 <= mask <= 32:
                return mask
        except ValueError:
            try:
                addr = IPv4Address(value)
                binary_str = bin(int(addr))[2:].zfill(32)
                if '01' not in binary_str:
                    return binary_str.count('1')
            except (AddressValueError, ValueError):
                pass
        raise argparse.ArgumentTypeError('')

    def format_output(self, results):
        if not results:
            return ''

        max_key_length = max(len(key) for key in results.keys()) + 1
        output = []

        for key, value in results.items():
            if value is None:
                continue

            if isinstance(value, str):
                parts = value.split(' ', 1)
                if len(parts) > 1 and parts[1].startswith('(2'):
                    value = parts[0]

            if '<tt>' in str(value):
                parts = value.split('<tt>')
                output.append(f"{key:{max_key_length}}: {parts[0].strip()}")
                for part in parts[1:]:
                    output.append(f"{'':{max_key_length}}  {part.replace('</tt>', '').strip()}")
            else:
                output.append(f"{key:{max_key_length}}: {value}")

        return '\n'.join(output)

    def print_version(self):
        print(_('''netsleuth {version}
Copyright (C) 2024 Vladimir Kosolapov
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Please report bugs to: <https://github.com/vmkspv/netsleuth/issues>.''').format(version=self.version))
        sys.exit(0)

    def run(self):
        args = self.parser.parse_args()

        if args.version:
            self.print_version()

        self.calculator.set_show_binary(args.binary)
        self.calculator.set_show_hex(args.hex)
        results = self.calculator.calculate(args.ip_address, args.mask)
        print(self.format_output(results))

class TranslatedArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        kwargs['formatter_class'] = lambda prog: argparse.HelpFormatter(prog, max_help_position=32)
        super().__init__(*args, **kwargs)
        self.options_group = self.add_argument_group(_('options'))
        self.general_group = self.add_argument_group(_('general'))

    def format_help(self):
        self._positionals.title = _('positional arguments')
        return super().format_help().replace('usage:', _('usage:'))

    def error(self, message):
        print(f"{_('Error')}: {_('Invalid IP address or mask')}", file=sys.stderr)
        sys.exit(1)

def main(version):
    cli = CommandLineInterface(version)
    cli.run()

if __name__ == '__main__':
    main()
