# coding=utf-8
from __future__ import absolute_import, print_function
from octoprint.server import user_permission

import octoprint.plugin
import flask
import board
import digitalio


class GpioControlPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.RestartNeedingPlugin,
):

    def __init__(self):
        self.active_states = {'active_low': False, 'active_high': True}
        self.pin_states = {}

    def on_startup(self, *args, **kwargs):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True),
            dict(
                type="sidebar",
                custom_bindings=True,
                template="gpiocontrol_sidebar.jinja2",
                icon="map-signs",
            ),
        ]

    def get_assets(self):
        return dict(
            js=["js/gpiocontrol.js", "js/fontawesome-iconpicker.min.js"],
            css=["css/gpiocontrol.css", "css/fontawesome-iconpicker.min.css"],
        )

    def get_settings_defaults(self):
        return dict(gpio_configurations=[])

    def on_settings_save(self, data):
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Cleaned GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            pin = configuration["pin"]

            if pin:
                self._logger.info("setting up output setting save")
                processing_pin = digitalio.DigitalInOut(getattr(board, pin))
                processing_pin.direction = digitalio.Direction.OUTPUT
                processing_pin.deinit()

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        self._logger.info("Reloading GPIO pins settings after save")
        self.on_after_startup()

    def on_after_startup(self):
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Configured GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            pin = configuration["pin"]

            if pin:
                self._logger.info("setting up output after startup")
                self._setup_pin(pin, configuration["default_state"], configuration["active_mode"])

    def _get_pin_state(self, pin, configuration=None):
        if configuration is not None:
            gpio_pin_state = self.pin_states[pin]
            if self.pin_states[pin] != gpio_pin_state:
                self._logger.info("Different GPIO states #{}: {},{}".format(pin, gpio_pin_state, self.pin_states[pin]))
        return 'on' if self.pin_states[pin] else 'off'

    def _setup_pin(self, pin, default_state, active_mode):
        processing_pin = digitalio.DigitalInOut(getattr(board, pin))
        processing_pin.direction = digitalio.Direction.OUTPUT

        if default_state == "default_on":
            self.pin_states[pin] = True
            processing_pin.value = self.active_states[active_mode]
        elif default_state == "default_off":
            self.pin_states[pin] = False
            processing_pin.value = not self.active_states[active_mode]

    def get_api_commands(self):
        return dict(turnGpioOn=["id"], turnGpio
