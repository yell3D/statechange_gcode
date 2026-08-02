# statechange_gcode

A plugin for Kalico/Klipper that allows you to automatically run (queue) specific G-Code macros when your 3D printer changes states.

## Manual Installation

1. SSH into your printer's host machine (e.g., Raspberry Pi).
2. Clone this repository into your home directory
3. Put the python file into `~/klipper/klippy/plugins/` for Kalico or `~/klipper/klippy/extras/` for Klipper.
4. Restart Klipper

<ins>Kalico Example</ins>
```bash
cd ~
git clone https://github.com/yell3D/statechange_gcode.git
ln -s ~/statechange_gcode/statechange_gcode.py ~/klipper/klippy/plugins/statechange_gcode.py
sudo systemctl restart klipper
```

## Automatic Installation
Run this, it will clone the repo, auto detect Kalico/Klipper and do the installation

```
curl -s -L https://raw.githubusercontent.com/yell3D/statechange_gcode/refs/heads/master/install.sh | bash --
```

# Updates via Moonraker

```
[update_manager statechange_gcode]
type: git_repo
path: ~/statechange_gcode
origin: https://github.com/yell3D/statechange_gcode.git
managed_services: klipper
primary_branch: master
```


## Usage
```
[statechange_gcode]
verbose: False # Don't emit log messages to klippy.log
idle_gcode:
    # G-Code to run when the printer enters the idle state
    RESPOND MSG="statechange_gcode: Idle fired"

wakeup_gcode:
    # G-Code to run when the printer wakes up from idle (ready/printing)
    RESPOND MSG="statechange_gcode: Wakeup fired"
```
<ins>Yell's Note</ins>
A regular Idle_Timeout Macro is normally processed but it might be nice to have the same things in the same place.
(Re)starting Klipper is considered a transition from idle, therefore `wakeup_gcode` is fired.

Technically you can use `ready_gcode` and `printing_gcode` too but Klipper is weird AF.
It emits the "printing" idle_timeout state whenever any G-Code is actively executing and 
then go into "ready".
```
Idle/Ready > G28  > Printing > [homing action]   > Ready > [Idle timeout]
Idle/Ready > M84  > Printing > [disable Stepper] > Ready > [Idle timeout]
Idle/Ready > M106 > Printing > [throw error]     > Ready > [Idle timeout]
```

## Motivation
I like my pi's to be on powersave CPU governor when not in use. But right now there is no way to fire Gcode on a "wake".


## License
```
# ----------------------------------------------------------------------------
# COFFEEWARE LICENSE (Revision Y.311):
# Yell wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day and
# you think this stuff is worth it, you can buy me a coffee in return.
#
# Yell <xyellx@gmail.com> / Discord: .yell.
# ----------------------------------------------------------------------------
```
