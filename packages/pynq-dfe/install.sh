#!/usr/bin/env bash
# Install the dfe-v0.1.1 board release from its downloaded assets.
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
mounted=false
mountpoint -q /data && mounted=true
venv=/usr/local/share/pynq-venv
python=$venv/bin/python
site=$("$python" -Ic 'import sysconfig; print(sysconfig.get_path("purelib"))')
pkg=/data/pynq-dfe-v0.1.0
pth=$site/pynq-dfe-v0.1.0.pth
marker=.pynq-dfe-v0.1.0
exec 9>/run/lock/pynq-dfe-install.lock
flock -x 9
state=/var/lib/pynq-dfe-overlays
previous=
if [[ -f $state ]]; then
    previous=$(cat "$state")
elif $mounted && [[ -f $pkg/$marker ]]; then
    previous=$(cat "$pkg/$marker")
fi
if [[ -n $previous ]] && { $mounted || [[ $previous != /data/* || -z $dest ]]; }; then
    dest=${dest:-$previous}
    [[ $(realpath -m -- "$dest") == "$previous" ]] || die "uninstall from $previous before moving overlays"
fi
dest=${dest:-/data/overlays/dfe}
[[ $dest == /* ]] || die "overlay directory must be absolute"
dest=$(realpath -m -- "$dest")
[[ $dest != / && $dest != /data && $dest != "$pkg" && $dest != "$pkg/"* && $pkg != "$dest/"* ]] || die "choose a dedicated overlay directory"
$mounted && [[ -e $pkg && ! -f $pkg/$marker ]] && die "$pkg already exists and is unmanaged"
[[ ! -e $pth || $(cat "$pth") == "$pkg" ]] || die "unexpected path in $pth"
overlays=true
if [[ $dest == /data/* ]] && ! $mounted; then
    overlays=false
    echo "Warning: /data is not mounted. Skipping overlays. Rerun with the card mounted for deferred cleanup." >&2
fi
if $overlays && [[ -d $dest && ! -f $dest/$marker && -n $(ls -A -- "$dest") ]]; then
    die "$dest contains unmanaged files"
fi
if $uninstall; then
    rm -f -- "$pth"
    "$python" -Im pip --isolated uninstall --no-cache-dir -y xrfdc pynq-dfe
    for lib in "${libs[@]}"; do rm -f -- "$site/pynq_dfe/lib/$lib"; done
    rmdir --ignore-fail-on-non-empty "$site/pynq_dfe/lib" "$site/pynq_dfe" 2>/dev/null || true
    if $overlays && [[ -f $dest/$marker ]]; then
        for archive in "${archives[@]}"; do
            dir="$dest/${archive%.tar.xz}"
            while IFS= read -r file; do rm -f -- "$dir/$file"; done < <(tar -tJf "$archive")
            rmdir --ignore-fail-on-non-empty -- "$dir" 2>/dev/null || true
        done
        rm -f -- "$dest/$marker"
        rmdir --ignore-fail-on-non-empty -- "$dest"
    fi
    if $mounted && [[ -f $pkg/$marker ]]; then rm -rf -- "$pkg"; fi
    if $overlays; then rm -f -- "$state"; fi
    exit 0
fi
if $overlays; then
    parent=$dest
    while [[ ! -e $parent ]]; do parent=$(dirname -- "$parent"); done
    [[ $(stat -c %d "$parent") != "$(stat -c %d /)" ]] || die "overlays need a data volume outside eMMC root"
    mkdir -p -- "$dest"
fi
work=$(mktemp -d /dev/shm/pynq-dfe-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cp -- "${wheels[@]}" "$work/"
(
    cd "$work"
    TMPDIR=$work "$python" -Im pip --isolated install --no-cache-dir --no-index --no-deps --no-compile --ignore-installed "${wheels[@]}"
)
install -d "$site/pynq_dfe/lib"
install -m 755 "${libs[@]}" "$site/pynq_dfe/lib/"
rm -f -- "$pth"
if $mounted && [[ -f $pkg/$marker ]]; then rm -rf -- "$pkg"; fi
echo "Installed DFE software in $site."
$overlays || exit 0
printf '%s\n' "$dest" > "$state"
touch "$dest/$marker"
for archive in "${archives[@]}"; do
    dir="$dest/${archive%.tar.xz}"
    mkdir -p -- "$dir"
    tar -xJf "$archive" --no-same-owner -C "$dir"
    (cd "$dir" && sha256sum --strict -c artifacts.sha256)
done
echo "Installed overlays at $dest."
