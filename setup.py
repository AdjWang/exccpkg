from setuptools import setup

setup(
    name = 'dspkg',
    version = '1.0',
    description = 'A dead simple C++ package manager.',
    author = 'AdjWang',
    author_email = 'wwang230513@gmail.com',
    packages = ['dspkg'],
    install_requires = ['requests'],
)
