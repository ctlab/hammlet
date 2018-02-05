from setuptools import setup

from version import __version__

setup(
    name='HMMLE',
    version=__version__,
    description='Hybridization Models Maximum Likelihood Estimator',
    url='https://github.com/Lipen/hmmle',
    author='Konstantin Chukharev',
    author_email='lipen00@gmail.com',
    license='GNU GPLv3',
    python_requires='>=2.7, !=3.0.*',
    py_modules=['version'],
    packages=['hmmle'],
    install_requires=[
        'numpy',
        'scipy',
        'click',
        'colorama'
    ],
    entry_points={
        'console_scripts': [
            'hmmle = hmmle:cli',
        ]
    }
)
