# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import os
import platform
import sys
import sysconfig
from setuptools import setup, Extension

# base source directory
source_dir = os.path.join("src", "oracledb")

# determine the nanoarrow bridge dependent source files (included)
base_dir = os.path.join(source_dir, "interchange")
nanoarrow_bridge_depends = [
    os.path.join(base_dir, "nanoarrow", "nanoarrow.c"),
    os.path.join(base_dir, "nanoarrow", "nanoarrow.h"),
]
nanoarrow_bridge_pxd = os.path.join(base_dir, "nanoarrow_bridge.pxd")

# determine the base implementation dependent source files (included)
impl_dir = os.path.join(source_dir, "impl", "base")
base_depends = [
    os.path.join(impl_dir, n)
    for n in sorted(os.listdir(impl_dir))
    if n.endswith(".pyx")
]
base_pxd = os.path.join(source_dir, "base_impl.pxd")
base_depends.extend([base_pxd, nanoarrow_bridge_pxd])

# determine the thick mode dependent source files (included)
impl_dir = os.path.join(source_dir, "impl", "thick")
source_dirs = [
    os.path.join(impl_dir, "odpi", "src"),
    os.path.join(impl_dir, "odpi", "include"),
]
thick_depends = [
    os.path.join(d, n)
    for d in source_dirs
    for n in sorted(os.listdir(d))
    if n.endswith(".c") or n.endswith(".h")
]
thick_depends.extend(
    os.path.join(impl_dir, n)
    for n in sorted(os.listdir(impl_dir))
    if n.endswith(".pyx") or n.endswith(".pxd")
)
thick_depends.append(base_pxd)

# determine the thin mode dependent source files (included)
impl_dir = os.path.join(source_dir, "impl", "thin")
thin_depends = [
    os.path.join(impl_dir, n)
    for n in sorted(os.listdir(impl_dir))
    if n.endswith(".pyx") or n.endswith(".pxi") or n.endswith(".pxd")
]
thin_depends.append(base_pxd)

# if the platform is macOS:
#  - target the minimum OS version that current Python packages work with.
#    (Use 'otool -l /path/to/python' and look for 'version' in the
#    LC_VERSION_MIN_MACOSX section)
#  - add argument required for cross-compilation for both x86_64 and arm64
#    architectures if the python interpreter is a universal2 version.

extra_compile_args = os.environ.get("PYO_COMPILE_ARGS", "").split()
if sys.platform == "darwin":
    extra_compile_args.extend(["-mmacosx-version-min=10.9"])
    if "universal2" in sysconfig.get_platform():
        if platform.machine() == "x86_64":
            target = "arm64-apple-macos"
        else:
            target = "x86_64-apple-macos"
        extra_compile_args.extend(["-target", target])

setup(
    ext_modules=[
        Extension(
            "oracledb.base_impl",
            sources=["src/oracledb/base_impl.pyx"],
            include_dirs=["src/oracledb/interchange/nanoarrow"],
            depends=base_depends,
            extra_compile_args=extra_compile_args,
        ),
        Extension(
            "oracledb.thin_impl",
            sources=["src/oracledb/thin_impl.pyx"],
            include_dirs=["src/oracledb/interchange/nanoarrow"],
            depends=thin_depends,
            extra_compile_args=extra_compile_args,
        ),
        Extension(
            "oracledb.thick_impl",
            sources=["src/oracledb/thick_impl.pyx"],
            include_dirs=[
                "src/oracledb/impl/thick/odpi/include",
                "src/oracledb/interchange/nanoarrow",
            ],
            depends=thick_depends,
            extra_compile_args=extra_compile_args,
        ),
        Extension(
            "oracledb.interchange.nanoarrow_bridge",
            sources=["src/oracledb/interchange/nanoarrow_bridge.pyx"],
            include_dirs=["src/oracledb/interchange/nanoarrow"],
            depends=nanoarrow_bridge_depends,
            extra_compile_args=extra_compile_args,
        ),
    ]
)
