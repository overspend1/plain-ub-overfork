#!/bin/bash

# Copy service file to systemd directory
sudo cp userbot.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable userbot.service

echo "Service installed successfully!"
echo "To start the service: sudo systemctl start userbot"
echo "To check status: sudo systemctl status userbot"
echo "To view logs: sudo journalctl -u userbot -f"