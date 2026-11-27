#   Copyright (c) 2019, Xilinx, Inc.
#   SPDX-License-Identifier: BSD-3-Clause


import subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel


class PlatformWheel(bdist_wheel):
    """The ABI-mode shared library is independent of CPython's C API."""
    def run(self):
        subprocess.run(["bash", "build_runtime.sh"], check=True)
        super().run()

    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        return "py3", "none", super().get_tag()[2]


for required in ("config.py", "mts.py"):
    if not (Path("xrfdc") / required).is_file():
        raise RuntimeError(f"Missing xrfdc/{required}. See README for build steps.")


with open("README.md", encoding='utf-8') as fh:
    readme_lines = fh.readlines()[:]
long_description = (''.join(readme_lines))


setup(
    name="xrfdc",
    version='1.1.0',
    description="Driver for the RFSoC RF Data Converter IP",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Xilinx/PYNQ/tree/master/sdbuild/packages/xrfdc',
    license='BSD 3-Clause',
    cmdclass={"bdist_wheel": PlatformWheel},
    packages=['xrfdc'],
    package_data={
        '': ['*.py', '*.so', '*.c'],
    },
    install_requires=[
        'wurlitzer',
        'cffi>=1.15',
        'pynq>=4.0.0',
    ]
)
