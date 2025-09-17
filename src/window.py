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

from gi.repository import Adw, Gtk, GLib
from .calculator import IPCalculator

@Gtk.Template(resource_path='/io/github/vmkspv/netsleuth/window.ui')
class NetsleuthWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'NetsleuthWindow'

    ip_entry = Gtk.Template.Child()
    history_button = Gtk.Template.Child()
    mask_dropdown = Gtk.Template.Child()
    show_binary_switch = Gtk.Template.Child()
    show_hex_switch = Gtk.Template.Child()
    calculate_button = Gtk.Template.Child()
    fact_of_the_day_box = Gtk.Template.Child()
    fact_row = Gtk.Template.Child()
    results_group_main = Gtk.Template.Child()
    copy_all_button_main = Gtk.Template.Child()
    export_button_main = Gtk.Template.Child()
    results_box_main = Gtk.Template.Child()
    results_group = Gtk.Template.Child()
    copy_all_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    results_box = Gtk.Template.Child()
    results_stack = Gtk.Template.Child()
    empty_results = Gtk.Template.Child()
    main_content = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculator = IPCalculator()
        self.results = {}
        self.history_dialog = None
        self.setup_mask_dropdown()
        self.connect_signals()
        self.calculate_button.set_sensitive(False)
        self.history = self.load_history()

        if any(item.get('selected', False) for item in self.history):
            GLib.idle_add(self.check_selected_item)
        else:
            self.results_stack.set_visible_child(self.empty_results)
            self.setup_fact_of_the_day()

    def setup_mask_dropdown(self):
        masks = [f"{i} - {self.calculator.int_to_dotted_netmask(i)}" for i in range(33)]
        self.mask_dropdown.set_model(Gtk.StringList.new(masks))
        self.mask_dropdown.set_selected(24)

        expression = Gtk.PropertyExpression.new(Gtk.StringObject, None, "string")
        self.mask_dropdown.set_expression(expression)

    def connect_signals(self):
        self.calculate_button.connect("clicked", self.on_calculate_clicked)
        self.show_binary_switch.connect("notify::active", self.on_show_binary_changed)
        self.show_hex_switch.connect("notify::active", self.on_show_hex_changed)
        self.ip_entry.connect("changed", self.on_ip_entry_changed)
        self.ip_entry.get_delegate().connect("activate", self.on_ip_entry_activate)
        self.ip_entry_timeout_id = None

        if self.split_view:
            self.split_view.connect('notify::collapsed', self.on_split_view_state_changed)

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

        new_item = {'ip': ip, 'mask': mask, 'selected': False}
        self.history = [item for item in self.history if not (item['ip'] == ip and item['mask'] == mask)]
        self.history.insert(0, new_item)
        self.history = self.history[:20]

        self.save_history()

        results = self.calculator.calculate(ip, mask)
        self.results = results
        self.display_results(results)
        self.fact_of_the_day_box.set_visible(False)

        if self.split_view:
            self.update_results_visibility(self.split_view.get_collapsed())

        if self.history_dialog:
            self.update_history_list()
        self.update_clear_button_state()

    def display_results(self, results):
        self.results_stack.set_visible_child(self.results_stack.get_last_child())

        while self.results_box.get_first_child():
            self.results_box.remove(self.results_box.get_first_child())
        while self.results_box_main.get_first_child():
            self.results_box_main.remove(self.results_box_main.get_first_child())

        def create_result_row(key, value):
            if value is None:
                return None
            subtitle = str(value)
            if key == _('Total Hosts'):
                count, *math = subtitle.split(' ', 1)
                subtitle = f"{count}{' ' + math[0] if math else ''}"
            row = Adw.ActionRow(title=key, subtitle=subtitle, subtitle_selectable=True)
            row.add_css_class("property-row")

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

        for key, value in results.items():
            row = create_result_row(key, value)
            if row:
                row_clone = create_result_row(key, value)
                self.results_box.append(row)
                self.results_box_main.append(row_clone)

        self.results_group.set_opacity(0)
        self.results_group_main.set_opacity(0)
        self.fade_in_results()

    def fade_in_results(self):
        for group in [self.results_group, self.results_group_main]:
            target = Adw.PropertyAnimationTarget.new(group, "opacity")
            animation = Adw.TimedAnimation.new(group, 0, 1, 350, target)
            animation.set_easing(Adw.Easing.EASE_OUT_CUBIC)
            animation.play()

    def on_show_binary_changed(self, switch, pspec):
        self.calculator.set_show_binary(switch.get_active())
        if self.results_group_main.get_visible() or self.results_group.get_visible():
            self.on_calculate_clicked(None)

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
        self.calculate_button.set_sensitive(self.is_valid_ip(valid_text))
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

    def on_ip_entry_activate(self, entry):
        if self.is_valid_ip(self.ip_entry.get_text()) and self.calculate_button.get_sensitive():
            self.on_calculate_clicked(None)

    @Gtk.Template.Callback()
    def on_history_button_clicked(self, button):
        if not self.history_dialog:
            self.history_dialog = self.create_history_dialog()
        self.update_history_list()
        self.history_dialog.present(self)

    def create_history_dialog(self):
        dialog = Adw.Dialog()
        dialog.set_title(_('History'))
        dialog.set_size_request(350, 400)

        toolbar_view = Adw.ToolbarView()

        header_bar = Adw.HeaderBar()
        header_bar.add_css_class("flat")

        self.clear_button = Gtk.Button(
            icon_name="user-trash-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_('Clear')
        )
        self.clear_button.add_css_class("flat")
        self.clear_button.add_css_class("error")
        self.clear_button.connect("clicked", self.on_clear_history)
        header_bar.pack_start(self.clear_button)

        toolbar_view.add_top_bar(header_bar)

        self.history_list = Gtk.ListBox()
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.history_list.add_css_class("boxed-list")

        self.empty_history_page = Adw.StatusPage(
            icon_name="document-open-recent-symbolic",
            title=_('No History'),
            description=_('Your calculation history will appear here')
        )

        self.history_stack = Gtk.Stack()
        self.history_stack.add_named(self.history_list, "history")
        self.history_stack.add_named(self.empty_history_page, "empty")

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(22)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.append(self.history_stack)

        scrolled_window = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            vexpand=True,
            child=content_box
        )

        toolbar_view.set_content(scrolled_window)

        self.history_toast_overlay = Adw.ToastOverlay()
        self.history_toast_overlay.set_child(toolbar_view)

        dialog.set_child(self.history_toast_overlay)

        return dialog

    def update_clear_button_state(self):
        if hasattr(self, 'clear_button'):
            self.clear_button.set_sensitive(bool(self.history))

    def update_history_list(self):
        while self.history_list.get_first_child():
            self.history_list.remove(self.history_list.get_first_child())

        if not self.history:
            self.history_stack.set_visible_child_name("empty")
            self.update_clear_button_state()
            return

        self.history_stack.set_visible_child_name("history")

        for item in self.history:
            title = f"{item['ip']}/{item['mask']}"
            mask_string = self.mask_dropdown.get_model().get_string(item['mask']).split('-', 1)[1].strip()

            row = Adw.ActionRow(
                title=title,
                subtitle=mask_string,
                activatable=True
            )
            row.connect("activated", self.on_history_item_activated, item)

            use_button = Gtk.Button(
                icon_name="object-select-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text=_('Select')
            )
            use_button.add_css_class("flat")
            use_button.connect("clicked", self.on_history_item_activated, item)
            row.add_suffix(use_button)

            self.history_list.append(row)

        self.update_clear_button_state()

    def on_history_item_activated(self, widget, item):
        self.ip_entry.set_text(item['ip'])
        self.mask_dropdown.set_selected(item['mask'])
        self.history_dialog.close()
        self.on_calculate_clicked(None)
        self.show_toast(_('Calculated: {ip}/{mask}').format(ip=item['ip'], mask=item['mask']))

    def on_clear_history(self, button):
        self.history.clear()
        self.save_history()
        self.update_history_list()
        toast = Adw.Toast.new(_('History cleared'))
        toast.set_timeout(2)
        self.history_toast_overlay.add_toast(toast)
        self.update_clear_button_state()

    def save_history(self):
        config_dir = GLib.get_user_config_dir()
        app_config_dir = path.join(config_dir, "netsleuth")
        makedirs(app_config_dir, exist_ok=True)
        history_file = path.join(app_config_dir, "history.json")

        with open(history_file, 'w') as f:
            dump(self.history, f, indent=4, ensure_ascii=False)

    def load_history(self):
        config_dir = GLib.get_user_config_dir()
        history_file = path.join(config_dir, "netsleuth", "history.json")

        if path.exists(history_file):
            with open(history_file, 'r') as f:
                return load(f)
        return []

    def check_selected_item(self):
        selected_item = None

        for item in self.history:
            if item.get('selected', False):
                selected_item = item
                break

        if selected_item:
            self.history.remove(selected_item)
            self.history.insert(0, selected_item)
            self.ip_entry.set_text(selected_item['ip'])
            self.mask_dropdown.set_selected(selected_item['mask'])
            self.on_calculate_clicked(None)
            self.show_toast(_('Calculated: {ip}/{mask}').format(ip=selected_item['ip'], mask=selected_item['mask']))
            selected_item['selected'] = False
            self.save_history()

    def do_close_request(self):
        self.save_history()
        return False

    @Gtk.Template.Callback()
    def on_copy_all_clicked(self, button):
        if not hasattr(self, "results") or not self.results:
            return

        text = "\n".join(f"{key}: {self.format_value(value, exclude_math=True)}"
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

        dialog = Gtk.FileChooserNative.new(
            title=_('Export results'),
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.set_current_name("results.json")

        filter_json = Gtk.FileFilter()
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)

        dialog.connect("response", self.on_export_response)
        dialog.show()

    def format_value_for_export(self, value):
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

    def on_export_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            file_path = file.get_path()
            file_name = file.get_basename()

            mappings = {
                _('Address'): 'Address',
                _('Netmask'): 'Netmask',
                _('Wildcard'): 'Wildcard',
                _('Network'): 'Network',
                _('Broadcast'): 'Broadcast',
                _('First Host'): 'First Host',
                _('Last Host'): 'Last Host',
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

            export_results = {
                mappings.get(key, key): (
                    mappings.get(value, value) if mappings.get(key, key) == 'Category' and isinstance(value, str)
                    else self.format_value_for_export(value)
                )
                for key, value in self.results.items()
                if value is not None
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                dump(export_results, f, ensure_ascii=False, indent=2)

            self.show_toast(_('Saved to {file}').format(file=file_name))

        dialog.destroy()

    def update_results_visibility(self, is_collapsed):
        if is_collapsed:
            self.results_group_main.set_visible(True)
            self.results_group.set_visible(False)
            self.split_view.set_show_content(False)
        else:
            self.results_group_main.set_visible(False)
            self.results_group.set_visible(True)
            self.split_view.set_show_content(True)

    def on_split_view_state_changed(self, split_view, pspec):
        if not hasattr(self, 'results') or not self.results:
            return

        self.update_results_visibility(split_view.get_collapsed())
