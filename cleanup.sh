#!/bin/bash

sudo apt clean
sudo apt autoclean
sudo apt autoremove -y
sudo journalctl --vacuum-time=7d
current_kernel=$(uname -r)
dpkg -l 'linux-image-*' | awk '{ print $2 }' | grep -v "$current_kernel" | grep -E 'linux-image-[0-9]+' | xargs sudo apt -y purge
sudo rm -rf /tmp/*
sudo rm -rf ~/.cache/thumbnails/*
sudo rm -rf ~/.cache/*
for user in /home/*; do
    sudo rm -rf "$user/.local/share/Trash/*/**"
done
sudo apt -y purge snapd apport ufw popularity-contest
sudo apt update
