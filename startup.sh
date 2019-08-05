#!/bin/bash

source ~/homecontrol.env
source ~/venv/homecontrol/bin/activate

if [ ! -e ~/homecontrol.log ]; then
	mkdir ~/homecontrol.log
fi

if tmux list-sessions | grep -E '^homecontrol:'; then
	tmux kill-session -t homecontrol
fi

tmux new-session -d -s homecontrol -n shell   "/bin/bash"
tmux new-window -t homecontrol -n fritzlog    "python ~/homecontrol/fritzlog.py; read"
tmux new-window -t homecontrol -n gardenlight "python ~/homecontrol/gardenlight.py; read"
tmux new-window -t homecontrol -n colorlight  "python ~/homecontrol/colorlight.py; read"
tmux new-window -t homecontrol -n gardenwater "python ~/homecontrol/watervalve.py; read"
tmux new-window -t homecontrol -n thermostat  "python ~/homecontrol/thermostat.py; read"
#tmux new-window -t homecontrol -n starlight   "python ~/homecontrol/starlight.py; read"
