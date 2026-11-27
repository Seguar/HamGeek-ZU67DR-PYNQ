"""Own the coordinator lock across SSH staging, validation and confirmed cleanup."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile


def launch_failure(output, fake, name, exc):
    record = dict(check=name, measured=repr(exc), expected="success", status="FAIL")
    (output/"launch-error.json").write_text(json.dumps(record)+"\n")
    report = dict(mode="offline fake" if fake else "board", status="FAIL", checks=[record])
    (output/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(output/"report.json", name, exc, file=sys.stderr)
    return 1


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--board", metavar="SSH_ALIAS")
    p.add_argument("--ssh-config", type=Path)
    p.add_argument("--lock", type=Path)
    p.add_argument("--adc-avcc", type=float, required=True)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--wheel", type=Path, help="install this wheel into the private board stage")
    p.add_argument("--board-python", default="/usr/local/share/pynq-venv/bin/python")
    p.add_argument("--stage-root", default="/data", choices=["/dev/shm", "/data"])
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.board and (not args.lock or args.lock.name != "BOARD.lock"):
        p.error("board mode requires the campaign --lock path ending in BOARD.lock")
    if args.board and args.board.startswith("-"):
        p.error("invalid SSH alias")
    args.output.mkdir(exist_ok=False, parents=True)
    lock = args.lock if args.board else args.output/"BOARD.lock"
    ticket = f"xrfdc-validation {datetime.now(timezone.utc).isoformat()} {secrets.token_hex(16)}"
    try:
        with lock.open("x") as f:
            f.write(ticket+"\n")
    except OSError as exc:
        return launch_failure(args.output, args.dry_run, "acquire campaign lock", exc)
    safe = True
    try:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as temp:
            stage = Path(temp)
            for name in ("validate.py", "fake.py"):
                shutil.copy(Path(__file__).with_name(name), stage/name)
            # Copy only members of the pinned manifest, never arbitrary local imports.
            from validate import MANIFEST, digest
            manifest = args.bundle/"artifacts.sha256"
            if digest(manifest) != MANIFEST:
                raise ValueError("unexpected acceptance manifest")
            bundle = stage/"bundle"
            bundle.mkdir()
            shutil.copy(manifest, bundle)
            for line in manifest.read_text().splitlines():
                shutil.copy(args.bundle/line.split()[1], bundle)
            shutil.copy(lock, stage/"BOARD.lock")
            argv = ["validate.py", "--ticket", ticket, "--adc-avcc", str(args.adc_avcc)]
            if args.dry_run:
                subprocess.run([sys.executable, *argv, "--fake"], cwd=stage)
            else:
                if args.wheel:
                    shutil.copy(args.wheel, stage / args.wheel.name)
                ssh = ["ssh", "-o", "BatchMode=yes"]
                if args.ssh_config:
                    ssh += ["-F", str(args.ssh_config)]
                ssh += [args.board]
                def remote(cmd, **kwargs):
                    return subprocess.run([*ssh, cmd], check=True, **kwargs)
                remote_stage = remote("mktemp -d "+args.stage_root+"/xrfdc.XXXXXXXX",
                                      capture_output=True, text=True).stdout.strip()
                if not remote_stage.startswith(args.stage_root+"/xrfdc."):
                    raise RuntimeError("unexpected stage path")
                print("Board stage", remote_stage, flush=True)
                prefix = "cd "+shlex.quote(remote_stage)+" && "
                with tempfile.TemporaryFile() as archive:
                    subprocess.run(["tar", "-C", temp, "-cf", "-", "."], stdout=archive, check=True)
                    archive.seek(0)
                    remote(prefix+"tar -xf -", stdin=archive)
                if lock.read_text().strip() != ticket:
                    raise RuntimeError("coordinator lock changed")
                env = []
                if args.wheel:
                    remote(prefix + shlex.join([args.board_python, "-B", "-m", "pip",
                           "install", "--no-index", "--no-cache-dir", "--disable-pip-version-check",
                           "--no-deps", "--no-compile", "--target", "site", "./"+args.wheel.name]))
                    env = ["env", "PYTHONPATH="+remote_stage+"/site"]
                safe = False
                # Always fetch the report for an ordinary validation failure.
                password = os.environ.get("BOARD_SUDO_PASSWORD")
                sudo = ["sudo", "-S", "-p", ""] if password else ["sudo", "-n"]
                proc = subprocess.run([*ssh, prefix+shlex.join(
                    [*sudo, "bash", "-ec",
                     'source /etc/profile.d/xrt_setup.sh; '
                     'export LD_LIBRARY_PATH="$XILINX_XRT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; '
                     'exec timeout -k 15 180 "$@"', "validation",
                     *env, args.board_python, "-B", *argv])],
                    input=(password+"\n").encode() if password else b"")
                report = remote(prefix+"cat report.json", capture_output=True).stdout
                (stage/"report.json").write_bytes(report)
                parsed = json.loads(report)
                for i, rec in enumerate(parsed["checks"], 1):
                    (stage/f"{i:03}.json").write_text(json.dumps(rec)+"\n")
                safe = any(r["check"] == "final idle" and r["status"] == "PASS"
                           for r in parsed["checks"]) or not any(
                               r["check"] == "r5 address map" for r in parsed["checks"])
                if safe:
                    remote(prefix+"rm -- BOARD.lock")
                if proc.returncode and parsed["status"] == "PASS":
                    raise RuntimeError("SSH/worker status differs from report")
            for result in stage.glob("*.json"):
                shutil.copy(result, args.output)
            summary = json.loads((args.output/"report.json").read_text())
            released = safe and lock.read_text().strip() == ticket
            if released:
                lock.unlink()
            rec = dict(check="campaign lock released", measured=released, expected=True,
                       status="PASS" if released else "FAIL")
            summary["checks"].append(rec)
            if not released:
                summary["status"] = "FAIL"
            (args.output/f"{len(summary['checks']):03}.json").write_text(json.dumps(rec)+"\n")
            (args.output/"report.json").write_text(json.dumps(summary, indent=2)+"\n")
            print(args.output/"report.json", summary["status"])
            return int(summary["status"] != "PASS")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return launch_failure(args.output, args.dry_run, "staging or report retrieval", exc)
    finally:
        if safe and lock.exists() and lock.read_text().strip() == ticket:
            lock.unlink()
        elif args.board and lock.exists():
            print("Confirm board idle before releasing the coordinator lock", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
