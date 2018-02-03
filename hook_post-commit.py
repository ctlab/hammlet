import re
import sys
import subprocess

regex_tag = re.compile(r'v?(.+)-(\d+)-g(\w+)')
regex_version = re.compile('^__version__ = [\'\"]([^\'\"]*)[\'\"]', re.M)
filename_version = 'version.py'


def get_bumped_version():
    # Get the version using "git describe".
    cmd = 'git describe --tags --long --always'
    try:
        tag = subprocess.check_output(cmd, shell=True).decode().strip()
    except subprocess.CalledProcessError:
        print('Unable to get version number from git tags', file=sys.stderr)
        exit(1)

    if tag.count('-') < 2:
        return '0+unknown'
    release, revision, commit = regex_tag.match(tag).groups()

    # PEP440
    version = release
    if int(revision) > 0:
        version += '.post' + revision
    version += '.dev0'

    return version


if __name__ == '__main__':
    bumped_version = get_bumped_version()

    with open(filename_version) as f:
        m = regex_version.search(f.read())
    if m:
        old_version = m.group(1)
    else:
        old_version = ''

    if bumped_version != old_version:
        with open(filename_version, 'w') as f:
            f.write('__version__ = \'%s\'\n' % bumped_version)
        print('post-commit hook: bumped version %s to %s' %
              (old_version, bumped_version), file=sys.stderr)

        # Index updated file with bumped version
        subprocess.call('git add %s' % filename_version, shell=True)
    else:
        print('post-commit hook: no need to bump version %s' % old_version, file=sys.stderr)
