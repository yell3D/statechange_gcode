# A plugin for Kalico/Klipper that allows you to automatically run (queue)
# specific G-Code macros when your 3D printer changes states.
#
# Example config:
#
# [statechange_gcode]
# verbose: False # Don't emit log messages to klippy.log
# idle_gcode:
#     # G-Code to run when the printer enters the idle state
#     RESPOND MSG="statechange_gcode: Idle fired"
#
# wakeup_gcode:
#     # G-Code to run when the printer wakes up from idle (ready/printing)
#     RESPOND MSG="statechange_gcode: Wakeup fired"
#
#
# __Yell's Note__
# A regular Idle_Timeout Macro is normally processed but it might be nice to have the same things in the same place.
# (Re)starting Klipper is considered a transition from idle, therefore `wakeup_gcode` is fired.
#
# Technically you can use `ready_gcode` and `printing_gcode` too but Klipper is weird AF.
# It emits the "printing" idle_timeout state whenever any G-Code is actively executing and
# then go into "ready".
#
#   Idle/Ready > G28  > Printing > [homing action]   > Ready > [Idle timeout]
#   Idle/Ready > M84  > Printing > [disable Stepper] > Ready > [Idle timeout]
#   Idle/Ready > M106 > Printing > [throw error]     > Ready > [Idle timeout]
#
# ----------------------------------------------------------------------------
# COFFEEWARE LICENSE (Revision Y.311):
# Yell wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day and
# you think this stuff is worth it, you can buy me a coffee in return.
#
# Yell <xyellx@gmail.com> / Discord: .yell.
# ----------------------------------------------------------------------------

import logging

VERSION = "1.0.0"
LOG_PREFIX = "[Statechange Gcode]"

class StatechangeGcode:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object("gcode")

        self._last_state = None # "idle", "ready", "printing"
        self._seen_first_event = False

        gcode_macro_obj = self.printer.load_object(config, "gcode_macro")
        self.verbose = config.getboolean("verbose", False)

        self.wake_template = gcode_macro_obj.load_template(config, "wakeup_gcode", "")
        self.idle_template = gcode_macro_obj.load_template(config, "idle_gcode", "")
        self.ready_template  = gcode_macro_obj.load_template(config, "ready_gcode", "")
        self.printing_template = gcode_macro_obj.load_template(config, "printing_gcode", "")

        # Only bother scheduling a callback for states that actually have gcode defined.
        # load_template uses TemplateWrapper and idk how to tell if empty
        self.has_wake = bool(config.get("wakeup_gcode", "").strip())
        self.has_idle = bool(config.get("idle_gcode", "").strip())
        self.has_ready = bool(config.get("ready_gcode", "").strip())
        self.has_printing = bool(config.get("printing_gcode", "").strip())

        self.printer.register_event_handler("idle_timeout:idle", self._handle_idle)
        self.printer.register_event_handler("idle_timeout:ready", self._handle_ready)
        self.printer.register_event_handler("idle_timeout:printing", self._handle_printing)

    def _log(self, msg):
        if self.verbose:
            logging.info(f"{LOG_PREFIX} {msg}")

    def _maybe_wake(self, new_state):
      if self._last_state == "idle" and new_state in ("ready", "printing"):
          if self.has_wake:
              self._log(f"Waking up from idle to {new_state}")
              self.reactor.register_callback(self._run_wake)
      self._last_state = new_state

    def _handle_idle(self, print_time):
        self._log("Entering Idle state")
        self._last_state = "idle"
        if self.has_idle:
            self.reactor.register_callback(self._run_idle)

    def _handle_ready(self, print_time):
        self._log("Entering Ready state")
        self._maybe_wake("ready")
        if self.has_ready:
            self.reactor.register_callback(self._run_ready)

    def _handle_printing(self, print_time):
        if not self._seen_first_event:
            self._seen_first_event = True
            self._last_state = "idle"
            self._log("Printer startup")
            return
        self._log("Entering Printing state")
        self._maybe_wake("printing")
        if self.has_printing:
            self.reactor.register_callback(self._run_printing)

    def _run_wake(self, eventtime):
        self._execute(self.wake_template, "wake")

    def _run_idle(self, eventtime):
        self._execute(self.idle_template, "idle")

    def _run_ready(self, eventtime):
        self._execute(self.ready_template, "ready")

    def _run_printing(self, eventtime):
        self._execute(self.printing_template, "printing")

    def _execute(self, template, state):
        try:
            script = template.render()
            if script and script.strip():
                self.gcode.run_script(script)
        except Exception as e:
            msg = f"{LOG_PREFIX} Error executing {state} template: {e}"
            logging.exception(msg)
            self.gcode.respond_info(msg)


def load_config(config):
    logging.info(f"{LOG_PREFIX} Initialized v{VERSION}")
    return StatechangeGcode(config)
