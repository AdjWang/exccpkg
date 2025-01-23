from setuptools import setup

setup(
    name = 'expkg',
    version = '1.0',
    description = 'An explicit C++ package builder.',
    author = 'AdjWang',
    author_email = 'wwang230513@gmail.com',
    packages = ['expkg'],
    install_requires = ['requests'],
)
