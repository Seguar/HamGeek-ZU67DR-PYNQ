#!/usr/bin/env bash
# Install the dfe-v0.1.0 board release from its downloaded assets.
set -euo pipefail
die() { echo "install.sh: $*" >&2; exit 1; }
uninstall=false
dest=
while (($#)); do
    case $1 in
        --uninstall) uninstall=true ;;
        --overlay-dir) shift; dest=${1:?missing overlay directory} ;;
        *) die "usage: install.sh [--uninstall] [--overlay-dir /absolute/path]" ;;
    esac
    shift
done
[[ $EUID == 0 ]] || die "run with sudo"
cd -- "$(dirname -- "$0")"
wheels=(xrfdc-1.1.0-py3-none-linux_aarch64.whl pynq_dfe-0.1.0-py3-none-any.whl)
libs=(libxdfe{ccf,equ,mix,ofdm,prach}.so)
archives=(dfe-{cfr,dpd,equ,fft,mixer-ccf,ofdm,prach,resampler-nlf}.tar.xz)
diff -u <(printf '%s\n' install.sh "${wheels[@]}" "${libs[@]}" "${archives[@]}" | LC_ALL=C sort) \
    <(awk '{print $2}' SHA256SUMS | LC_ALL=C sort)
sha256sum --strict -c SHA256SUMS
free=$(df -m --output=avail / | tail -1)
(( free >= 60 )) || die "eMMC root needs 60 MB free (available $free MB)"
mountpoint -q /data || die "mount the data partition at /data first"
venv=/usr/local/share/pynq-venv
python=$venv/bin/python
site=$("$python" -Ic 'import sysconfig; print(sysconfig.get_path("purelib"))')
pkg=/data/pynq-dfe-v0.1.0
pth=$site/pynq-dfe-v0.1.0.pth
marker=.pynq-dfe-v0.1.0
exec 9>/run/lock/pynq-dfe-install.lock
flock -x 9
if [[ -f $pkg/$marker ]]; then
    previous=$(cat "$pkg/$marker")
    dest=${dest:-$previous}
    [[ $(realpath -m -- "$dest") == "$previous" ]] || die "uninstall from $previous before moving overlays"
fi
dest=${dest:-/data/overlays/dfe}
[[ $dest == /* ]] || die "overlay directory must be absolute"
dest=$(realpath -m -- "$dest")
[[ $dest != /data && $dest != "$pkg" && $dest != "$pkg/"* && $pkg != "$dest/"* ]] || die "choose a dedicated overlay directory"
[[ ! -e $pkg || -f $pkg/$marker ]] || die "$pkg already exists and is unmanaged"
[[ ! -e $pth || $(cat "$pth") == "$pkg" ]] || die "unexpected path in $pth"
if [[ -d $dest && ! -f $dest/$marker && -n $(ls -A -- "$dest") ]]; then
    die "$dest contains unmanaged files"
fi
if $uninstall; then
    rm -f -- "$pth"
    if [[ -f $dest/$marker ]]; then
        for archive in "${archives[@]}"; do
            dir="$dest/${archive%.tar.xz}"
            while IFS= read -r file; do rm -f -- "$dir/$file"; done < <(tar -tJf "$archive")
            rmdir --ignore-fail-on-non-empty -- "$dir" 2>/dev/null || true
        done
        rm -f -- "$dest/$marker"
        rmdir --ignore-fail-on-non-empty -- "$dest"
    fi
    if [[ -f $pkg/$marker ]]; then rm -rf -- "$pkg"; fi
    exit 0
fi
mkdir -p -- "$dest"
[[ $(stat -c %d "$dest") != "$(stat -c %d /)" ]] || die "overlays need a data volume outside eMMC root"
work=$(mktemp -d /data/.pynq-dfe-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
if [[ ! -f $pkg/$marker ]]; then
    TMPDIR=$work "$python" -Im pip --isolated install --no-cache-dir --no-index --no-deps \
        --no-compile --target "$work/python" "${wheels[@]}"
    install -d "$work/python/pynq_dfe/lib"
    install -m 755 "${libs[@]}" "$work/python/pynq_dfe/lib/"
    printf '%s\n' "$dest" > "$work/python/$marker"
    chmod 755 "$work/python"
    mv -T -- "$work/python" "$pkg"
fi
touch "$dest/$marker"
for archive in "${archives[@]}"; do
    dir="$dest/${archive%.tar.xz}"
    mkdir -p -- "$dir"
    tar -xJf "$archive" --no-same-owner -C "$dir"
    (cd "$dir" && sha256sum --strict -c artifacts.sha256)
done
printf '%s\n' "$pkg" > "$pth"
echo "Installed in $venv with packages at $pkg and overlays at $dest."
