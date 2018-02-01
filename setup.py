from setuptools import setup

setup(
    name='HMMLE',
    version='1.0.0',
    description='Hybridization Models Maximum Likelihood Estimator',
    url='https://github.com/Lipen/hmmle',
    author='Konstantin Chukharev',
    author_email='lipen00@gmail.com',
    py_modules=['hmmle'],
    install_requires=[
        'numpy',
        'scipy',
        'Click',
    ],
    extras_require={
        'dev': ['colorama']
    },
    entry_points={
        'console_scripts': [
            'hmmle = hmmle:cli',
        ]
    }
)
