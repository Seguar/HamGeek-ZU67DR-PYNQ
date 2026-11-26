#!/bin/bash
set -euo pipefail

if (( EUID != 0 || $# != 4 )); then
    echo "Usage: sudo $0 RC1_RAW_IMAGE standard|8GB WHEELHOUSE NEW_OUTPUT_DIRECTORY" >&2
    exit 2
fi

scripts=$(cd -- "$(dirname -- "$0")" && pwd)
input=$(realpath -e -- "$1")
wheelhouse=$(realpath -e -- "$3")
[[ -f $input && -d $wheelhouse ]]
case "$2" in
    standard)
        input_hash=eaf551158e9e9a57c57dfc2cb423772df4e42dac4e13d5f93bb701680c8bb45b
        suffix=
        disk_id=67d20271
        ;;
    8GB)
        input_hash=f3b7633a6233f39324e8fe223b0502e2f45fcfee8ed261ed9f83934f6136361b
        suffix=-8GB
        disk_id=67d20272
        ;;
    *) exit 2 ;;
esac
printf '%s  %s\n' "$input_hash" "$input" | sha256sum -c -
mkdir -- "$4"
cd -- "$4"
image=HamGeekZU67DR-PYNQ-4.0.0-rc2${suffix}.img
cp --reflink=auto --sparse=always -- "$input" "$image"
sfdisk --disk-id "$image" "0x$disk_id"
sfdisk --verify "$image"

mkdir boot root
loop=
cleanup() {
    if mountpoint -q root; then umount root; fi
    if mountpoint -q boot; then umount boot; fi
    if [[ -n $loop ]]; then losetup -d "$loop"; fi
    rmdir root boot
}
trap cleanup EXIT
loop=$(losetup --find --show --partscan "$image")
udevadm settle
boot_part=${loop}p1
root_part=${loop}p2
[[ $(blkid -p -s PART_ENTRY_UUID -o value "$boot_part") == "$disk_id-01" ]]
[[ $(blkid -p -s PART_ENTRY_UUID -o value "$root_part") == "$disk_id-02" ]]
fatlabel -i "$boot_part" "${disk_id^^}"
if e2fsck -fp "$root_part" > root-precheck.log 2>&1; then
    :
else
    [[ $? == 1 ]]
fi
tune2fs -U "$disk_id-720f-48fc-aa4c-d8aa02205026" "$root_part"
mount "$boot_part" boot
mount "$root_part" root
sha256sum boot/{BOOT.BIN,Image} > firmware.sha256

printf '438b8c762f5dcd22bb1de2b1ced14d8e0084bebec6da4c00050e75cbe1a8c2ca  boot/system.dtb\n' | sha256sum -c -
mmc=$(fdtget -t s boot/system.dtb /aliases mmc0)
[[ $mmc == /axi/mmc@ff170000 ]]
dtc -q -s -I dtb -O dts -o rc1.dts boot/system.dtb
fdtput boot/system.dtb "$mmc" disable-wp
dtc -q -s -I dtb -O dts -o rc2.dts boot/system.dtb
diff -u rc1.dts rc2.dts > dtb.diff || [[ $? == 1 ]]
[[ $(grep -Ec '^[-+][[:space:]]' dtb.diff) == 1 ]]
grep -Eq '^\+[[:space:]]+disable-wp;' dtb.diff
bootargs=$(fdtget -t s boot/system.dtb /chosen bootargs)
[[ $bootargs == "root=/dev/mmcblk0p2 "* ]]
grep -Eq '^[[:space:]]+fdt /system[.]dtb[[:space:]]*$' boot/extlinux/extlinux.conf
! grep -qiE '^[[:space:]]*(append|initrd)[[:space:]]' boot/extlinux/extlinux.conf
printf '    append root=PARTUUID=%s-02 %s\n' "$disk_id" "${bootargs#* }" >> boot/extlinux/extlinux.conf

touch root/etc/fstab
! grep -Eq '^[^#]+[[:space:]]/boot[[:space:]]' root/etc/fstab
printf 'PARTUUID=%s-01 /boot vfat defaults,nofail,x-systemd.device-timeout=10s 0 0\n' "$disk_id" >> root/etc/fstab
install -m 0755 "$scripts/resizefs.sh" "$scripts/bootpy.sh" root/usr/local/bin/
install -d root/etc/systemd/system/bootpy.service.d
printf '[Unit]\nRequiresMountsFor=/boot\n' > root/etc/systemd/system/bootpy.service.d/boot-mount.conf

# Compile the spidev sdist with the image's AArch64 toolchain and install offline.
install -d -m 0700 root/tmp/rc2-deps
install -m 0644 "$wheelhouse"/* "$scripts/clock-deps.txt" root/tmp/rc2-deps/
unshare --net chroot root /usr/bin/env HOME=/tmp PIP_CONFIG_FILE=/dev/null \
    /usr/local/share/pynq-venv/bin/python -m pip install \
    --no-index --find-links=/tmp/rc2-deps --no-deps --no-build-isolation \
    --no-cache-dir --require-hashes -r /tmp/rc2-deps/clock-deps.txt
rm -r -- root/tmp/rc2-deps
sha256sum -c firmware.sha256
cp boot/extlinux/extlinux.conf root/etc/fstab ./
df -B1 --output=size,used,avail root > initial-headroom.txt
umount root
umount boot
fsck.fat -n "$boot_part" > fat-fsck.log
e2fsck -fn "$root_part" > root-fsck.log 2>&1
sfdisk --json "$image" > partitions.json
printf 'Image prepared: %s\n' "$image"
