# Simple ActionNetwork integration

Update ActionNetwork subscriptions hourly using lists in a Google sheet.

## Install

    git clone [THIS REPO]

    python3 -mvenv env
    . ./activate
    pip install -r requirements.txt

Ensure `../credentials/action_network.py` and `../credentials/XXX.json` (service worker key) exist.

## Add service

    DEST=~/.config/systemd/user
    mkdir -p $DEST
    ln -sf $(pwd)/actionnetwork.service $DEST
    ln -sf $(pwd)/actionnetwork.timer $DEST
    systemctl --user daemon-reload

## Enable service

    sudo loginctl enable-linger $USER
    systemctl --user enable --now actionnetwork.timer
