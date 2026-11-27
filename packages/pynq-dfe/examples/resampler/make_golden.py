"""Regenerate golden.npz using ./golden linked against the PG392 Linux C model."""
from pathlib import Path
import subprocess

import numpy as np
from model import BEATS, stimulus


def main():
    vectors = {}
    for name, lanes in (("dec", 3), ("intp", 1)):
        kinds = ("impulse", "tone", "alias") if lanes == 3 else ("impulse", "tone")
        for kind in kinds:
            x = np.tile(stimulus(lanes, kind), 3)
            iq = np.column_stack((x.real, x.imag)).astype("<i2")
            output = subprocess.run(["./golden", name], input=iq.tobytes(),
                                    capture_output=True, check=True)
            y = np.frombuffer(output.stdout, dtype="<i2").reshape(3, 2*BEATS, 2)[-1]
            vectors[f"{name}_{kind}"] = y[:, 0] + 1j*y[:, 1]
    np.savez_compressed(Path(__file__).with_name("golden.npz"), **vectors)


if __name__ == "__main__":
    main()
