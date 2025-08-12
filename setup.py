# build: python3 -m pip install --upgrade build && python3 -m build
# upload: twine upload --repository pypi dist/*
from setuptools import setup

setup(
    name = 'exccpkg',
    version = '3.0.2',
    # shutil.rmtree onexc https://docs.python.org/3/library/shutil.html#shutil.rmtree
    python_requires='>=3.12',
    description = 'An explicit C++ package builder.',
    author = 'AdjWang',
    author_email = 'wwang230513@gmail.com',
    packages = ['exccpkg'],
    install_requires = ['requests'],
)
