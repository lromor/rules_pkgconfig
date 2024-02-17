from collections import namedtuple
import argparse
import subprocess
import pathlib


BUILD_FILE_CONTENTS = """cc_import(
    name = "{name}",
    shared_library = "{shared_library}",
    includes = {includes}
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
    if not lib_path:
        lib_path = '/usr/lib'
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



def generate(args):
    info = get_pkg_info(args.name)
    includes = '[\n'
    for include in info.includes:
        includes += f'        "{include}",\n'
    includes += '    ],'

    # Check for the existance of the library .so
    shared_library = pathlib.Path(info.lib_path) / ('lib' + info.lname + '.so')
    if not shared_library.exists() and not shared_library.is_file():
        raise RuntimeError(f'library {shared_library} does not exist')

    name = args.name
    version = info.version
    with open("BUILD.generated", 'w') as f:
        f.write(BUILD_FILE_CONTENTS.format(
            name=name,
            includes=includes,
            shared_library=shared_library,
        ))

    with open("MODULE.bazel.generated", 'w') as f:
        f.write(MODULE_FILE_CONTENTS.format(name=name, version=version))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of the local package')
    parser.set_defaults(func=generate)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
