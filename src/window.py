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

from gi.repository import Adw, Gtk, Gdk, GLib
from .calculator import IPCalculator

@Gtk.Template(resource_path='/io/github/vmkspv/netsleuth/window.ui')
class NetsleuthWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'NetsleuthWindow'

    ip_entry = Gtk.Template.Child()
    mask_dropdown = Gtk.Template.Child()
    show_binary_switch = Gtk.Template.Child()
    calculate_button = Gtk.Template.Child()
    results_box = Gtk.Template.Child()
    results_group = Gtk.Template.Child()
    main_content = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Netsleuth")
        self.calculator = IPCalculator()
        self.setup_mask_dropdown()
        self.calculate_button.connect("clicked", self.on_calculate_clicked)
        self.show_binary_switch.connect("notify::active", self.on_show_binary_changed)

    def setup_mask_dropdown(self):
        masks = [f"{i} - {self.calculator.int_to_dotted_netmask(i)}" for i in range(33)]
        self.mask_dropdown.set_model(Gtk.StringList.new(masks))
        self.mask_dropdown.set_selected(24)

    @Gtk.Template.Callback()
    def on_calculate_clicked(self, button):
        ip = self.ip_entry.get_text()
        mask = int(self.mask_dropdown.get_selected_item().get_string().split()[0])
        results = self.calculator.calculate(ip, mask)
        self.display_results(results)

    def display_results(self, results):
        while self.results_box.get_first_child():
            self.results_box.remove(self.results_box.get_first_child())

        for key, value in results.items():
            row = Adw.ActionRow(title=key, subtitle=str(value))
            row.add_css_class("property-row")

            copy_button = Gtk.Button(icon_name="edit-copy-symbolic")
            copy_button.add_css_class("flat")
            copy_button.connect("clicked", self.on_copy_clicked, str(value))
            row.add_suffix(copy_button)

            self.results_box.append(row)

        if not self.results_group.get_visible():
            self.results_group.set_visible(True)
            self.results_group.set_opacity(0)
            self.fade_in_results()

        self.scroll_to_results()

    def fade_in_results(self):
        target = Adw.PropertyAnimationTarget.new(self.results_group, "opacity")
        animation = Adw.TimedAnimation.new(
            self.results_group,
            0,
            1,
            300,
            target
        )
        animation.play()

    def scroll_to_results(self):
        def on_map(widget):
            adjustment = self.main_content.get_vadjustment()
            target = Adw.PropertyAnimationTarget.new(adjustment, "value")
            animation = Adw.TimedAnimation.new(
                adjustment,
                adjustment.get_value(),
                adjustment.get_upper() - adjustment.get_page_size(),
                500,
                target
            )
            animation.play()
            widget.disconnect(self.scroll_handler_id)

        self.scroll_handler_id = self.results_group.connect("map", on_map)

    def on_show_binary_changed(self, switch, pspec):
        self.calculator.set_show_binary(switch.get_active())
        if self.results_group.get_visible():
            self.show_toast("Recalculation needed")

    @Gtk.Template.Callback()
    def on_about_button_clicked(self, button):
        self.get_application().on_about_action(None, None)

    def on_copy_clicked(self, button, text):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)
        self.show_toast("Copied to clipboard")

    def show_toast(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)
