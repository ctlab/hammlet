import sys
from setuptools import setup

from version import __version__


def main():
    install_requires = [
        'numpy',
        'scipy',
        'click',
    ]
    if sys.platform == 'win32':
        install_requires.append('colorama')

    setup_requires = []
    if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
        setup_requires.append('pytest-runner')

    setup(
        name='Hammlet',
        version=__version__,
        description='Hybridization Models Maximum Likelihood Estimator',
        url='https://github.com/ctlab/hammlet',
        author='Konstantin Chukharev',
        author_email='lipen00@gmail.com',
        license='GNU GPLv3',
        python_requires='>=2.7, !=3.0.*',
        py_modules=['version'],
        packages=['hammlet'],
        install_requires=install_requires,
        setup_requires=setup_requires,
        tests_require=['pytest'],
        entry_points={
            'console_scripts': [
                'hammlet = hammlet.main:cli',
            ]
        }
    )


if __name__ == '__main__':
    main()
