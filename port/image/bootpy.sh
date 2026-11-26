#!/bin/bash
# The bootpy unit orders this script after the FAT mount declared in fstab.
. /etc/environment
for f in /etc/profile.d/*.sh; do source "$f"; done

set -eu
read -ra boot_args < /proc/cmdline
for arg in "${boot_args[@]}"; do
    if [[ $arg =~ ^root=PARTUUID=([0-9a-f]{8})-02$ ]]; then
        disk_id=${BASH_REMATCH[1]}
        break
    fi
done
: "${disk_id:?Root partition ID is missing}"
boot_dev=$(findmnt -rn -o SOURCE --mountpoint /boot)
[[ $(blkid -p -s PART_ENTRY_UUID -o value "$boot_dev") == "$disk_id-01" ]]

if [[ -f /boot/boot.py ]]; then
    python3 /boot/boot.py
fi
