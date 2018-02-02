from setuptools import setup

from version import get_version

setup(
    name='HMMLE',
    version=get_version(),
    description='Hybridization Models Maximum Likelihood Estimator',
    url='https://github.com/Lipen/hmmle',
    author='Konstantin Chukharev',
    author_email='lipen00@gmail.com',
    py_modules=['version'],
    packages=['hmmle'],
    install_requires=[
        'numpy',
        'scipy',
        'Click',
        'colorama'
    ],
    entry_points={
        'console_scripts': [
            'hmmle = hmmle:cli',
        ]
    }
)
