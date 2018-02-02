__all__ = ('get_version', )

import re
import subprocess

regex_version = re.compile(r'v?(.+)-(\d+)-g(\w+)(-dirty)?')


def get_version():
    # Get the version using "git describe".
    cmd = 'git describe --tags --long --dirty --always'
    try:
        git_version = subprocess.check_output(cmd, shell=True).decode().strip()
    except subprocess.CalledProcessError:
        print('Unable to get version number from git tags')
        exit(1)

    if git_version.count('-') < 2:
        return '0.0.0'
    release, revision, commit, dirty = regex_version.match(git_version).groups()

    version = release
    if revision != '0':
        version += '.post' + revision
    if dirty:
        version += '.dev1'

    return version

if __name__ == '__main__':
    print(get_version())
