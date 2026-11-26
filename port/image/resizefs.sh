#!/bin/bash
set -euo pipefail

if grep -qx 'RESIZED=1' /etc/environment; then
    exit 0
fi

# Use the kernel's mounted-root device number. SOURCE may be /dev/root.
root_dev=$(readlink -e "/sys/dev/block/$(findmnt -rn -o MAJ:MIN --mountpoint /)")
part_name=${root_dev##*/}
disk_name=$(basename "$(dirname "$root_dev")")
[[ $disk_name =~ ^mmcblk[0-9]+$ && $part_name == "${disk_name}p2" ]]
[[ $root_dev == */ff160000.mmc/* || $root_dev == */ff170000.mmc/* ]]
[[ $(findmnt -rn -o FSTYPE --mountpoint /) == ext4 ]]
disk=/dev/$disk_name
part=/dev/$part_name
partuuid=$(blkid -p -s PART_ENTRY_UUID -o value "$part")
[[ $partuuid =~ ^[0-9a-f]{8}-02$ ]]
grep -Fqw "root=PARTUUID=$partuuid" /proc/cmdline

# growpart returns 1 for an already-full disk. A retry can still need resize2fs.
if output=$(LC_ALL=C growpart --fudge 0 "$disk" 2 2>&1); then
    printf '%s\n' "$output"
else
    status=$?
    printf '%s\n' "$output" >&2
    [[ $status == 1 && $output == NOCHANGE:* ]]
fi

# Refresh the kernel's view only when it still differs from the on-disk table.
sectors=$(partx --raw --noheadings -o SECTORS --nr 2 "$disk")
if [[ $(cat "$root_dev/size") != "$sectors" ]]; then
    partx --update --nr 2 "$disk"
    [[ $(cat "$root_dev/size") == "$sectors" ]]
fi
resize2fs "$part"

# Keep the compact image's policy of preserving at least 256 MiB for users.
available=$(df -B1 --output=avail /var | tail -n 1)
if (( available >= 384 * 1024 * 1024 )) && [[ ! -e /var/swap ]]; then
    if (umask 077; fallocate -l 128M /var/swap) &&
       chmod 600 /var/swap && mkswap /var/swap && swapon /var/swap; then
        if ! grep -qE '^/var/swap[[:space:]]' /etc/fstab; then
            printf '/var/swap none swap sw 0 0\n' >> /etc/fstab
        fi
    else
        rm -f -- /var/swap
        printf 'Swap setup failed\n' >&2
    fi
fi
printf '\nRESIZED=1\n' >> /etc/environment
