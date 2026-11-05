# window.py
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

from os import path, makedirs
from json import dump, load
from random import choice

from gi.repository import Adw, Gtk, Gio, GLib
from .calculator import IPCalculator

@Gtk.Template(resource_path='/io/github/vmkspv/netsleuth/window.ui')
class NetsleuthWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'NetsleuthWindow'

    toast_overlay = Gtk.Template.Child()
    navigation_view = Gtk.Template.Child()
    split_view = Gtk.Template.Child()

    ip_entry = Gtk.Template.Child()
    mask_dropdown = Gtk.Template.Child()
    show_binary_switch = Gtk.Template.Child()
    show_hex_switch = Gtk.Template.Child()
    calculate_button = Gtk.Template.Child()

    fact_of_the_day_box = Gtk.Template.Child()
    fact_row = Gtk.Template.Child()

    results_group_main = Gtk.Template.Child()
    results_box_main = Gtk.Template.Child()

    results_stack = Gtk.Template.Child()
    empty_results = Gtk.Template.Child()
    results_group = Gtk.Template.Child()
    results_box = Gtk.Template.Child()

    vlsm_ip_entry = Gtk.Template.Child()
    vlsm_history_button = Gtk.Template.Child()
    vlsm_mask_dropdown = Gtk.Template.Child()
    vlsm_subnets_box = Gtk.Template.Child()
    vlsm_calculate_button = Gtk.Template.Child()

    vlsm_results_group = Gtk.Template.Child()
    vlsm_results_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculator = IPCalculator()
        self.results = {}
        self.vlsm_results = []
        self.subnet_rows = []
        self.ip_entry_timeout_id = None
        self.setup_mask_dropdown()
        self.calculate_button.set_sensitive(False)
        self.vlsm_calculate_button.set_sensitive(False)
        self.history = self.load_history()
        self.results_stack.set_visible_child(self.empty_results)
        self.setup_fact_of_the_day()

    def setup_mask_dropdown(self):
        masks = [f"{i} - {self.calculator.int_to_dotted_netmask(i)}" for i in range(33)]
        model = Gtk.StringList.new(masks)
        expression = Gtk.PropertyExpression.new(Gtk.StringObject, None, "string")

        for dropdown in (self.mask_dropdown, self.vlsm_mask_dropdown):
            dropdown.set_model(model)
            dropdown.set_selected(24)
            dropdown.set_expression(expression)

    def setup_fact_of_the_day(self):
        facts = [
            _('The 0.0.0.0 address is used to represent the default route or an unknown target network.'),
            _('A PTR record enables reverse DNS lookup, translating an IP address back to a domain name.'),
            _('The 240.0.0.0/4 block was originally reserved for future experiments, but is now considered legacy.'),
            _('In a /30 subnet, there are only 2 usable IP addresses, often used for point-to-point links.'),
            _('Wildcard mask inverts subnet masks, providing flexible IP filtering in access lists.'),
            _('An IP\'s binary representation always has 32 bits, regardless of the decimal notation used.')
        ]
        fact = choice(facts)
        self.fact_of_the_day_box.set_visible(True)
        self.fact_row.set_subtitle(fact)

    @Gtk.Template.Callback()
    def on_calculate_clicked(self, button=None):
        ip = self.ip_entry.get_text()
        mask = int(self.mask_dropdown.get_selected_item().get_string().split()[0])

        self.add_history_item({"ip": ip, "mask": mask})

        results = self.calculator.calculate(ip, mask)
        self.results = results
        self.display_results(results)
        self.fact_of_the_day_box.set_visible(False)

        if self.split_view:
            self.update_results_visibility(self.split_view.get_collapsed())

    def display_results(self, results):
        self.results_stack.set_visible_child(self.results_stack.get_last_child())

        while self.results_box.get_first_child():
            self.results_box.remove(self.results_box.get_first_child())
        while self.results_box_main.get_first_child():
            self.results_box_main.remove(self.results_box_main.get_first_child())

        for key, value in results.items():
            row = self.create_result_row(key, value)
            if row:
                row_clone = self.create_result_row(key, value)
                self.results_box.append(row)
                self.results_box_main.append(row_clone)

        self.results_group.set_opacity(0)
        self.results_group_main.set_opacity(0)
        self.fade_in_results()

    def create_result_row(self, key, value):
        if value is None:
            return None
        subtitle = str(value)
        if key == _('Total Hosts'):
            count, *math = subtitle.split(' ', 1)
            subtitle = f"{count}{' ' + math[0] if math else ''}"
        row = Adw.ActionRow(title=key, subtitle=subtitle, subtitle_selectable=True)
        row.add_css_class("property")

        copy_button = Gtk.Button(
            icon_name="edit-copy-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_('Copy')
        )
        copy_button.add_css_class("flat")
        copy_value = value.replace('<tt>', '').replace('</tt>', '') if isinstance(value, str) else str(value)
        copy_button.connect("clicked", self.on_copy_clicked, copy_value)

        row.add_suffix(copy_button)
        return row

    def fade_in_results(self):
        for group in [self.results_group, self.results_group_main]:
            target = Adw.PropertyAnimationTarget.new(group, "opacity")
            animation = Adw.TimedAnimation.new(group, 0, 1, 350, target)
            animation.set_easing(Adw.Easing.EASE_OUT_CUBIC)
            animation.play()

    @Gtk.Template.Callback()
    def on_show_binary_changed(self, switch, pspec):
        self.calculator.set_show_binary(switch.get_active())
        if self.results_group_main.get_visible() or self.results_group.get_visible():
            self.on_calculate_clicked(None)

    @Gtk.Template.Callback()
    def on_show_hex_changed(self, switch, pspec):
        self.calculator.set_show_hex(switch.get_active())
        if self.results_group_main.get_visible() or self.results_group.get_visible():
            self.on_calculate_clicked(None)

    def on_copy_clicked(self, button, text):
        if '<tt>' in text:
            parts = text.split('<tt>')
            text = f"{parts[0].strip()} {parts[1].replace('</tt>', '').strip()}"
        clipboard = self.get_clipboard()
        clipboard.set(text)
        self.show_toast(_('Copied to clipboard'))

    def show_toast(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

    @Gtk.Template.Callback()
    def on_ip_entry_changed(self, entry):
        if self.ip_entry_timeout_id:
            GLib.source_remove(self.ip_entry_timeout_id)
        self.ip_entry_timeout_id = GLib.timeout_add(0, self.delayed_ip_validation, entry)

    def delayed_ip_validation(self, entry):
        text = entry.get_text()
        valid_text = self.validate_ip_input(text)
        if valid_text != text:
            entry.set_text(valid_text)
            entry.set_position(-1)
        button = self.calculate_button if entry == self.ip_entry else self.vlsm_calculate_button
        button.set_sensitive(self.is_valid_ip(valid_text))
        self.ip_entry_timeout_id = None
        return GLib.SOURCE_REMOVE

    def validate_ip_input(self, text):
        parts = [''.join(filter(str.isdigit, part))[:3] for part in text.split('.')[:4]]
        valid_parts = [str(min(int(p), 255)) for p in parts if p]
        result = '.'.join(valid_parts)
        if text.endswith('.') and len(valid_parts) < 4:
            result += '.'
        return result

    def is_valid_ip(self, ip):
        octets = ip.split('.')
        if len(octets) != 4:
            return False
        for octet in octets:
            if not octet or not octet.isdigit() or int(octet) > 255:
                return False
        return True

    @Gtk.Template.Callback()
    def on_ip_entry_activate(self, entry):
        button = self.calculate_button if entry == self.ip_entry else self.vlsm_calculate_button
        if self.is_valid_ip(entry.get_text()) and button.get_sensitive():
            button.emit("clicked")

    @Gtk.Template.Callback()
    def on_history_button_clicked(self, button):
        planner = button == self.vlsm_history_button
        history = [item for item in self.history if ("subnets" in item) == planner]

        history_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        history_list.add_css_class("boxed-list-separate")
        history_list.add_css_class("history-list")

        empty_page = Adw.StatusPage(
            icon_name="document-open-recent-symbolic",
            title=_('No History'),
            description=_('Your calculation history will appear here')
        )

        stack = Gtk.Stack()
        stack.add_named(history_list, "history")
        stack.add_named(empty_page, "empty")

        dialog = Adw.Dialog()
        dialog.set_title(_('History'))
        dialog.set_content_width(350)
        dialog.set_content_height(400)

        toast_overlay = Adw.ToastOverlay()

        clear_button = Gtk.Button(
            icon_name="user-trash-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_('Clear'),
            sensitive=bool(history)
        )
        clear_button.add_css_class("flat")
        clear_button.add_css_class("error")
        clear_button.connect("clicked", lambda btn: self.on_clear_history(
            history_list, stack, clear_button, toast_overlay, planner, dialog
        ))

        header_bar = Adw.HeaderBar()
        header_bar.pack_start(clear_button)

        content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=16, margin_bottom=16, margin_start=16, margin_end=16
        )
        content_box.append(stack)

        scrolled = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            vexpand=True,
            child=content_box
        )

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header_bar)
        toolbar_view.set_content(scrolled)

        toast_overlay.set_child(toolbar_view)
        dialog.set_child(toast_overlay)

        if history:
            stack.set_visible_child_name("history")
            for item in history:
                history_list.append(self.create_history_row(item, dialog))
        else:
            stack.set_visible_child_name("empty")

        dialog.present(self)
        dialog.grab_focus()

    def create_history_row(self, item, dialog):
        title = f"{item['ip']}/{item['mask']}"
        if "subnets" in item:
            subtitle = ', '.join(name or _('Subnet {number}').format(number=number)
                                 for number, (name, hosts) in enumerate(item['subnets'], 1))
        else:
            subtitle = self.mask_dropdown.get_model().get_string(item['mask']).split('-', 1)[1].strip()

        row = Adw.ActionRow(
            title=title, subtitle=GLib.markup_escape_text(subtitle),
            subtitle_lines=1, activatable=True
        )
        row.connect("activated", lambda r: self.on_history_item_activated(item, dialog))

        arrow = Gtk.Image(icon_name="go-next-symbolic")
        arrow.add_css_class("dimmed")
        row.add_suffix(arrow)

        return row

    def on_history_item_activated(self, item, dialog):
        dialog.close()
        if "subnets" in item:
            self.vlsm_ip_entry.set_text(item['ip'])
            self.vlsm_mask_dropdown.set_selected(item['mask'])
            self.clear_subnet_rows()
            for name, hosts in item['subnets']:
                self.on_add_subnet_clicked()
                self.subnet_rows[-1].set_text(name)
                self.subnet_rows[-1].hosts_spin.set_value(hosts)
            self.on_vlsm_calculate_clicked(None)
        else:
            self.ip_entry.set_text(item['ip'])
            self.mask_dropdown.set_selected(item['mask'])
            self.on_calculate_clicked(None)
        self.show_toast(_('Calculated: {ip}/{mask}').format(ip=item['ip'], mask=item['mask']))

    def add_history_item(self, new_item):
        planner = "subnets" in new_item
        same_mode = [item for item in self.history if ("subnets" in item) == planner and item != new_item]
        other_mode = [item for item in self.history if ("subnets" in item) != planner]
        self.history = ([new_item] + same_mode)[:25] + other_mode
        self.save_history()

    def on_clear_history(self, history_list, stack, clear_button, toast_overlay, planner, dialog):
        removed_items = [item for item in self.history if ("subnets" in item) == planner]
        self.history = [item for item in self.history if ("subnets" in item) != planner]
        self.save_history()

        history_list.remove_all()
        stack.set_visible_child_name("empty")
        clear_button.set_sensitive(False)

        def on_undo_clicked(toast):
            self.history = removed_items + self.history
            self.save_history()

            for item in removed_items:
                history_list.append(self.create_history_row(item, dialog))
            stack.set_visible_child_name("history")
            clear_button.set_sensitive(True)

        toast = Adw.Toast.new(_('History cleared'))
        toast.set_button_label(_('Undo'))
        toast.connect("button-clicked", on_undo_clicked)
        toast_overlay.add_toast(toast)

    def save_history(self):
        config_dir = GLib.get_user_config_dir()
        app_config_dir = path.join(config_dir, "netsleuth")
        makedirs(app_config_dir, exist_ok=True)
        history_file = path.join(app_config_dir, "history.json")

        with open(history_file, "w") as f:
            dump(self.history, f, indent=4, ensure_ascii=False)

    def load_history(self):
        config_dir = GLib.get_user_config_dir()
        history_file = path.join(config_dir, "netsleuth", "history.json")

        if path.exists(history_file):
            with open(history_file, "r") as f:
                return load(f)
        return []

    def do_close_request(self):
        self.save_history()
        return False

    @Gtk.Template.Callback()
    def on_copy_all_clicked(self, button):
        if not hasattr(self, "results") or not self.results:
            return

        text = '\n'.join(f"{key}: {self.format_value(value, exclude_math=True)}"
                        for key, value in self.results.items()
                        if value is not None)
        clipboard = self.get_clipboard()
        clipboard.set(text)
        self.show_toast(_('Copied to clipboard'))

    def remove_math_formula(self, value):
        if isinstance(value, str):
            parts = value.split(' ', 1)
            if len(parts) > 1 and parts[1].startswith('(2'):
                return parts[0]
        return value

    def format_value(self, value, exclude_math=False):
        if isinstance(value, str):
            if '<tt>' in value:
                parts = value.split('<tt>')
                formatted_parts = [parts[0].strip()]
                if len(parts) > 1:
                    formatted_parts.append(f"({parts[1].replace('</tt>', '').strip()})")
                if len(parts) > 2:
                    formatted_parts.append(f"({parts[2].replace('</tt>', '').strip()})")
                return ' '.join(formatted_parts)
        if exclude_math:
            return self.remove_math_formula(value)
        return str(value)

    @Gtk.Template.Callback()
    def on_export_clicked(self, button):
        if not hasattr(self, "results") or not self.results:
            return

        mappings = self.get_export_mappings()
        self.export_json({
            mappings.get(key, key): (
                mappings.get(value, value) if mappings.get(key, key) == 'Category' and isinstance(value, str)
                else self.format_for_export(value)
            )
            for key, value in self.results.items()
            if value is not None
        })

    def export_json(self, data):
        filter_json = Gtk.FileFilter()
        filter_json.add_mime_type("application/json")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_json)

        dialog = Gtk.FileDialog()
        dialog.set_title(_('Export results'))
        dialog.set_initial_name("results.json")
        dialog.set_default_filter(filter_json)
        dialog.set_filters(filters)

        dialog.save(self, None, self.on_export_finish, data)

    def on_export_finish(self, dialog, result, data):
        try:
            file = dialog.save_finish(result)
        except GLib.Error:
            return

        file_path = file.get_path()
        file_name = file.get_basename()

        with open(file_path, "w", encoding="utf-8") as f:
            dump(data, f, ensure_ascii=False, indent=2)

        toast = Adw.Toast.new(_('Saved to {file}').format(file=file_name))
        toast.set_button_label(_('Open'))
        toast.connect("button-clicked",
            lambda _, f=file: Gtk.FileLauncher.new(f).launch(self))
        self.toast_overlay.add_toast(toast)

    def get_export_mappings(self):
        return {
            _('Address'): 'Address',
            _('Netmask'): 'Netmask',
            _('Wildcard'): 'Wildcard',
            _('Network'): 'Network',
            _('Broadcast'): 'Broadcast',
            _('First Host'): 'First Host',
            _('Last Host'): 'Last Host',
            _('Required Hosts'): 'Required Hosts',
            _('Total Hosts'): 'Total Hosts',
            _('Category'): 'Category',
            _('PTR Record'): 'PTR Record',
            _('IPv4 Mapped Address'): 'IPv4 Mapped Address',
            _('6to4 Prefix'): '6to4 Prefix',
            _('Private (Class A)'): 'Private (Class A)',
            _('Private (Class B)'): 'Private (Class B)',
            _('Private (Class C)'): 'Private (Class C)',
            _('Loopback'): 'Loopback',
            _('Link-Local (APIPA)'): 'Link-Local (APIPA)',
            _('Multicast'): 'Multicast',
            _('Reserved'): 'Reserved',
            _('Public'): 'Public'
        }

    def format_for_export(self, value):
        if isinstance(value, str):
            if '<tt>' in value:
                parts = value.split('<tt>')
                remaining_parts = parts[1:]
                current_part = 0
                result = {'decimal': parts[0].strip()}

                if self.calculator.show_binary:
                    if current_part < len(remaining_parts):
                        result['binary'] = remaining_parts[current_part].replace('</tt>', '').strip()
                        current_part += 1

                if self.calculator.show_hex:
                    if current_part < len(remaining_parts):
                        result['hexadecimal'] = remaining_parts[current_part].replace('</tt>', '').strip()

                return result

        return self.remove_math_formula(value)

    def update_results_visibility(self, is_collapsed):
        if is_collapsed:
            self.results_group_main.set_visible(True)
            self.results_group.set_visible(False)
            self.split_view.set_show_content(False)
        else:
            self.results_group_main.set_visible(False)
            self.results_group.set_visible(True)
            self.split_view.set_show_content(True)

    @Gtk.Template.Callback()
    def on_split_view_state_changed(self, split_view, pspec):
        if not hasattr(self, "results") or not self.results:
            return

        self.update_results_visibility(split_view.get_collapsed())

    @Gtk.Template.Callback()
    def on_subnet_planner_activated(self, row):
        self.vlsm_ip_entry.set_text("")
        self.vlsm_mask_dropdown.set_selected(24)
        self.clear_subnet_rows()
        self.on_add_subnet_clicked()
        self.vlsm_results_group.set_visible(False)
        self.navigation_view.push_by_tag("vlsm")

    def clear_subnet_rows(self):
        for subnet_row in self.subnet_rows:
            self.vlsm_subnets_box.remove(subnet_row)
        self.subnet_rows.clear()

    @Gtk.Template.Callback()
    def on_add_subnet_clicked(self, button=None):
        row = Adw.EntryRow(title=_('Subnet {number}').format(number=len(self.subnet_rows) + 1))

        row.hosts_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=1, lower=1, upper=1, step_increment=1),
            numeric=True,
            width_chars=6,
            valign=Gtk.Align.CENTER,
            tooltip_text=_('Required Hosts')
        )

        row.remove_button = Gtk.Button(
            icon_name="list-remove-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_('Remove')
        )
        row.remove_button.add_css_class("flat")
        row.remove_button.connect("clicked", lambda btn: self.on_remove_subnet(row))

        row.add_suffix(row.hosts_spin)
        row.add_suffix(row.remove_button)
        row.remove_button.set_sensitive(bool(self.subnet_rows))
        if self.subnet_rows:
            self.subnet_rows[0].remove_button.set_sensitive(True)
        self.vlsm_subnets_box.insert(row, len(self.subnet_rows))
        self.subnet_rows.append(row)
        self.on_vlsm_mask_changed(self.vlsm_mask_dropdown)

    @Gtk.Template.Callback()
    def on_vlsm_mask_changed(self, dropdown, pspec=None):
        for row in self.subnet_rows:
            row.hosts_spin.set_range(1, max(2 ** (32 - dropdown.get_selected()) - 2, 1))

    def on_remove_subnet(self, row):
        self.subnet_rows.remove(row)
        self.vlsm_subnets_box.remove(row)
        for number, subnet_row in enumerate(self.subnet_rows, 1):
            subnet_row.set_title(_('Subnet {number}').format(number=number))
        if len(self.subnet_rows) == 1:
            self.subnet_rows[0].remove_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_vlsm_calculate_clicked(self, button):
        for row in self.subnet_rows:
            row.hosts_spin.update()
        subnets = [(row.get_text() or row.get_title(), row.hosts_spin.get_value_as_int())
                   for row in self.subnet_rows]
        results = self.calculator.calculate_vlsm(
            self.vlsm_ip_entry.get_text(), self.vlsm_mask_dropdown.get_selected(), subnets
        )
        if isinstance(results, dict):
            self.vlsm_results_group.set_visible(False)
            self.show_toast(results[_('Error')])
            return

        self.add_history_item({
            "ip": self.vlsm_ip_entry.get_text(),
            "mask": self.vlsm_mask_dropdown.get_selected(),
            "subnets": [[row.get_text(), row.hosts_spin.get_value_as_int()] for row in self.subnet_rows]
        })

        self.vlsm_results = results
        while self.vlsm_results_box.get_first_child():
            self.vlsm_results_box.remove(self.vlsm_results_box.get_first_child())

        for name, details in results:
            expander = Adw.ExpanderRow(title=GLib.markup_escape_text(name), subtitle=details[_('Network')])
            for key, value in details.items():
                expander.add_row(self.create_result_row(key, value))
            self.vlsm_results_box.append(expander)

        self.vlsm_results_group.set_visible(True)

    @Gtk.Template.Callback()
    def on_vlsm_copy_all_clicked(self, button):
        text = '\n\n'.join(
            f"{name}\n" + '\n'.join(f"{key}: {self.format_value(value, exclude_math=True)}"
                                    for key, value in details.items())
            for name, details in self.vlsm_results
        )
        clipboard = self.get_clipboard()
        clipboard.set(text)
        self.show_toast(_('Copied to clipboard'))

    @Gtk.Template.Callback()
    def on_vlsm_export_clicked(self, button):
        mappings = self.get_export_mappings()
        self.export_json([
            {'Name': name, **{mappings.get(key, key): self.remove_math_formula(value)
                              for key, value in details.items()}}
            for name, details in self.vlsm_results
        ])
