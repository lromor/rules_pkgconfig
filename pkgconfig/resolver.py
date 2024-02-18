#!/usr/bin/env python3
from collections import namedtuple
import argparse
import subprocess
import pathlib
import json
import os


BUILD_FILE_CONTENTS = """cc_import(
    name = "{name}",
    shared_library = "{shared_library}",
    includes = {includes}
    visibility = ["//visibility:public"],
    linkopts = {linkopts}
)
"""

MODULE_FILE_CONTENTS = """module(
    name = "{name}",
    version = "{version}",
)
"""


SystemPackageInfo = namedtuple(
    'SystemPackageMeta', [
        'version',
        'lname',
        'lib_path',
        'includes',
    ],
)

def get_pkg_info(name):
    version = subprocess.check_output([
        'pkg-config',
        '--modversion',
        name,
    ]).decode().strip()
    lname = subprocess.check_output([
        'pkg-config',
        '--libs-only-l',
        name,
    ]).decode().strip().removeprefix('-l')
    lib_path = subprocess.check_output([
        'pkg-config',
        '--libs-only-L',
        name,
    ]).decode().strip().removeprefix('-L')
    includes = map(lambda x: x.removeprefix('-I'), subprocess.check_output([
        'pkg-config',
        '--cflags-only-I',
        name,
    ]).decode().strip().split())

    return SystemPackageInfo(
        version=version,
        lname=lname,
        lib_path=lib_path,
        includes = includes,
    )


STANDARD_DEBIAN_PATHS = [
    '/usr/lib/x86_64-linux-gnu',
    '/usr/lib'
]


def generate(args):
    info = get_pkg_info(args.name)
    includes = '[\n'
    for include in info.includes:
        includes += f'        "{include}",\n'
    includes += '    ],'

    # Check for the existance of the library .so
    library_name = 'lib' + info.lname + '.so'
    lib_path = pathlib.Path(info.lib_path)

    results = list(filter(lambda x: x.exists() and x.is_file() , map(lambda x: lib_path / library_name, [lib_path] + STANDARD_DEBIAN_PATHS)))
    if len(results) == 0:
        raise RuntimeError(f'could not find {library_name}')

    shared_library = results[0]
    os.symlink(shared_library, library_name)

    rpath = shared_library.parent
    name = args.name
    version = info.version
    with open("BUILD", 'w') as f:
        f.write(BUILD_FILE_CONTENTS.format(
            name=name,
            includes=includes,
            shared_library=library_name,
            linkopts = f'["-Wl,-rpath {rpath}"]',
        ))

    with open("MODULE", 'w') as f:
        f.write(MODULE_FILE_CONTENTS.format(name=name, version=version))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of the local package')
    parser.set_defaults(func=generate)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
