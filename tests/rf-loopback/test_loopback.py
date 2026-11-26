"""Generate eight coherent DAC tones and optionally capture the ADC loopback."""
import argparse
from contextlib import nullcontext
from hashlib import file_digest
from pathlib import Path
import subprocess
from time import sleep
from xml.etree.ElementTree import ParseError

import numpy as np

from rfdc_config import fixed_dac_parameters


def coherent_program(frequencies_mhz, amplitude, zone):
    from waveform import DAC_RATE, DAC, Program, dac_segment, periodic_tone_length, tone

    wanted = np.asarray(frequencies_mhz) * 1e6
    source = np.minimum(wanted, DAC_RATE - wanted)
    segments, actual = {}, []
    for channel, frequency in enumerate(source):
        try:
            count = periodic_tone_length(frequency)
            programmed = frequency
        except ValueError:
            count = 4096 * DAC.per_word
            programmed = round(frequency * count / DAC_RATE) * DAC_RATE / count
            if not 0 < programmed < DAC_RATE / 2:
                raise ValueError(f"channel {channel}: tone is too close to a Nyquist edge")
        name = f"tone{channel}"
        segments[name] = dac_segment(name, tone(programmed, count, amplitude=amplitude))
        actual.append(programmed if zone == 1 else DAC_RATE - programmed)
    program = Program(DAC, segments.values())
    for channel, name in enumerate(segments):
        # Long repeats give the table reader time to prefetch the loop entry.
        program[channel].at_unit(name, 0, repeat=65536)
    return program.compile(), actual


def verify_overlay(bitfile):
    """Check the artifact pair and DAC mode before programming the board."""
    if bitfile.suffix != ".bit":
        raise ValueError("expected the overlay .bit file")
    hwh = bitfile.with_suffix(".hwh")
    manifest = bitfile.with_name("artifacts.sha256")
    entries = (line.split(maxsplit=1) for line in manifest.read_text().splitlines())
    hashes = {name: digest for digest, name in entries}
    for artifact in (bitfile, hwh):
        with artifact.open("rb") as stream:
            actual = file_digest(stream, "sha256").hexdigest()
        if hashes.get(artifact.name) != actual:
            raise ValueError(f"{artifact.name} does not match {manifest.name}")
    fixed_dac_parameters(hwh)
    return hwh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bitfile", type=Path)
    parser.add_argument("--mhz", type=float, nargs=8, default=[100, 200, 300, 400, 500, 600, 700, 800])
    parser.add_argument("--amplitude", type=float, default=0.1, help="fraction of full-scale code")
    parser.add_argument("--adc-avcc", type=float, required=True, help="measured TP16 rail in volts")
    parser.add_argument("--program-lmk", action="store_true")
    parser.add_argument("--vendor-vitis-zip", type=Path, help="your copy of adda_loop.zip")
    parser.add_argument("--dac-setup", type=Path, default=Path(__file__).with_name("dac-setup"))
    parser.add_argument("--adc-target", type=int, default=-1)
    parser.add_argument("--dac-target", type=int, default=-1)
    parser.add_argument("--dac-zone", type=int, choices=(1, 2), default=1)
    parser.add_argument("--tone-only-seconds", type=float, default=0)
    parser.add_argument("--output", type=Path, default=Path("rf_loopback.npz"))
    parser.add_argument("--status-only", action="store_true",
                        help="download and check PS-clocked status without accessing RFDC or DMA")
    args = parser.parse_args()
    if not 0 < args.amplitude <= 0.5 or not 0.980 <= args.adc_avcc <= 1.040:
        parser.error("use amplitude in (0, 0.5] and a measured in-spec ADC_AVCC")
    low, high = (0, 5000) if args.dac_zone == 1 else (5000, 10000)
    if not all(low < f < high for f in args.mhz):
        parser.error("all tones must be inside the selected Nyquist zone")
    if not np.isfinite(args.tone_only_seconds) or args.tone_only_seconds < 0:
        parser.error("tone-only duration must be finite and nonnegative")
    if args.dac_zone == 2 and args.tone_only_seconds <= 0:
        parser.error("zone 2 characterisation uses tone-only mode with a spectrum analyser")

    bitfile = args.bitfile.resolve()
    try:
        hwh = verify_overlay(bitfile)
    except (OSError, ParseError, ValueError) as exc:
        parser.error(str(exc))

    from clock_guard import progress, verify_bundle
    from loopback_driver import RfLoopback, check_hwh
    from lmk_spi import configured_clock
    from lmk_profile import profile_for_rate

    progress("Verify rf_control bundle and clock topology")
    verify_bundle(bitfile)
    if not check_hwh(hwh)[0]:
        raise RuntimeError("RF loopback HWH address map differs")
    program, actual = coherent_program(args.mhz, args.amplitude, args.dac_zone)
    progress("Program LMK profile and wait for PLL2" if args.program_lmk else "Use the current LMK profile")
    clock = nullcontext()
    if args.program_lmk:
        if args.vendor_vitis_zip is None:
            parser.error("--program-lmk requires --vendor-vitis-zip")
        clock = configured_clock(profile_for_rate(args.vendor_vitis_zip, 2.5, 480), log=progress)
    with clock:
        rt = RfLoopback(bitfile, expected_rate=2.5, expected_sysref=6.25,
                       status_only=args.status_only)
        if args.status_only:
            return
        try:
            measured = rt.clock_measurements
            progress("Align RfLoopback phase")
            rt.lock_phase(log=progress)
            progress("Start DAC and ADC MTS")
            progress(rt.mts(args.adc_target, args.dac_target).strip())
            progress("Set DAC Nyquist zone")
            setup = subprocess.run(
                [str(args.dac_setup.resolve()), "--nyquist-only", str(args.dac_zone)],
                capture_output=True, text=True, timeout=30,
            )
            if setup.returncode:
                raise RuntimeError(setup.stderr or setup.stdout)
            progress(setup.stdout.strip())
            progress("Load coherent DAC waveform")
            rt.load_program(program)
            progress(f"Programmed RF frequencies (MHz) {[f / 1e6 for f in actual]}")
            tone_only = bool(args.tone_only_seconds)
            progress("Arm tone playback and capture")
            rt.run(dac_loop=0xFF if tone_only else 0, adc_delay=64,
                   cap_words=0 if tone_only else None)
            if args.tone_only_seconds:
                sleep(args.tone_only_seconds)
                fault = rt.rd("FAULT")
                if fault:
                    raise RuntimeError(f"tone playback fault: {fault:#010x}")
            else:
                data = rt.capture_all()
                peak = np.max(np.abs(data.astype(np.int32)), axis=1) / 32768
                if np.any(peak >= 10 ** (-3 / 20)):
                    raise RuntimeError(f"ADC peak above -3 dBFS, per-channel fractions: {peak}")
                with args.output.open("xb") as output:
                    np.savez(output, samples=data, fs_hz=2.5e9, tone_hz=actual,
                             adc_avcc_v=args.adc_avcc, clocks=measured)
                progress(f"Captured {data.shape[0]} × {data.shape[1]} samples")
        finally:
            progress("Stop playback and capture")
            rt.stop()


if __name__ == "__main__":
    main()
