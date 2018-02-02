__all__ = ('get_version', )

import re
import subprocess
from os.path import dirname, isdir, join

regex_version = re.compile(r'v?(.+)-(\d+)-g(\w+)(-dirty)?')


def get_version():
    d = dirname(__file__)

    if isdir(join(d, '.git')):
        # Get the version using "git describe".
        cmd = 'git describe --tags --long --dirty --always'
        try:
            version = subprocess.check_output(cmd, shell=True).decode().strip()
        except subprocess.CalledProcessError:
            print('Unable to get version number from git tags')
            exit(1)

        if version.count('-') < 2:
            return '0.0.0'
        release, revision, commit, dirty = regex_version.match(version).groups()

        version = release
        if revision != '0':
            version += '.post' + revision
        if dirty:
            version += '.dev1'

    else:
        raise NotImplementedError()

    return version


if __name__ == '__main__':
    print(get_version())
