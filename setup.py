from setuptools import setup

setup(
    name='HMMLE',
    version='1.0.0',
    description='Hybridization Models Maximum Likelihood Estimator',
    author='Konstantin Chukharev',
    author_email='lipen00@gmail.com',
    py_modules=['hmmle', 'models'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'hmmle = hmmle:cli',
        ]
    }
)
