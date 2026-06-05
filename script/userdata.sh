#!/bin/bash

NEW_PORT=2022

echo "Port $NEW_PORT" | sudo tee /etc/ssh/sshd_config.d/10-custom-port.conf

sudo systemctl daemon-reload

sudo systemctl restart ssh.socket