import sys

from setuptools import find_packages, setup


def main():
    install_requires = [
        'numpy',
        'scipy',
        'click',
    ]
    if sys.platform == 'win32':
        install_requires.append('colorama')

    setup_requires = ['setuptools_scm']
    if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
        setup_requires.append('pytest-runner')

    setup(
        name='Hammlet',
        description='Hybridization Models Maximum Likelihood Estimator',
        url='https://github.com/ctlab/hammlet',
        author='Konstantin Chukharev',
        author_email='lipen00@gmail.com',
        license='GNU GPLv3',
        python_requires='>=2.7, !=3.0.*',
        package_dir={'': 'src'},
        packages=find_packages('src'),
        use_scm_version={
            'write_to': 'src/hammlet/version.py',
            'version_scheme': 'post-release',
            # 'local_scheme': lambda _: '',
            'local_scheme': 'dirty-tag',
        },
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
