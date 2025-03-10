from setuptools import setup

setup(
    name = 'exccpkg',
    version = '1.1',
    description = 'An explicit C++ package builder.',
    author = 'AdjWang',
    author_email = 'wwang230513@gmail.com',
    packages = ['exccpkg'],
    install_requires = ['requests'],
)
