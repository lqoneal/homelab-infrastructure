#!/bin/bash

set -e

BACKUP_DIR="$HOME/system_backup_$(date +%Y%m%d_%H%M%S)"

echo "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo "== Backing up system configuration =="

sudo cp /etc/fstab "$BACKUP_DIR/" 2>/dev/null || true
sudo cp /etc/default/grub "$BACKUP_DIR/" 2>/dev/null || true

echo "== Backing up EFI boot configuration =="

sudo efibootmgr -v > "$BACKUP_DIR/efiboot.txt" 2>/dev/null || true

echo "== Backing up installed package list =="

dpkg --get-selections > "$BACKUP_DIR/packages.txt" 2>/dev/null || true

apt-mark showmanual > "$BACKUP_DIR/manual_packages.txt" 2>/dev/null || true

echo "== Backing up user dev workspace =="

if [ -d "$HOME/dev" ]; then
    rsync -a --info=progress2 "$HOME/dev" "$BACKUP_DIR/dev/"
fi

echo "== Backing up SSH + Git config =="

if [ -d "$HOME/.ssh" ]; then
    rsync -a "$HOME/.ssh" "$BACKUP_DIR/ssh/"
fi

cp "$HOME/.gitconfig" "$BACKUP_DIR/" 2>/dev/null || true

echo "== System info snapshot =="

uname -a > "$BACKUP_DIR/system_info.txt"
lsblk -f > "$BACKUP_DIR/lsblk.txt"
df -h > "$BACKUP_DIR/disk_usage.txt"

echo "== DONE =="

echo "Backup stored at:"
echo "$BACKUP_DIR"
