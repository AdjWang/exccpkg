# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import tools

@dataclass
class DepInfo:
    download: Callable[[], Path]
    build: Callable[[Path], Path]
    install: Callable[[Path], None]


class DsPkg:
    def __init__(self, download_dir: Path, deps_dir: Path, install_dir: Path):
        self.__deps = []
        self.__download_dir = download_dir
        self.__deps_dir = deps_dir
        self.__install_dir = install_dir

    def add_dep(self, dep: DepInfo) -> None:
        self.__deps.append(dep)
    
    def resolve(self) -> None:
        tools.mkdirp(self.__download_dir)
        tools.mkdirp(self.__deps_dir)
        tools.mkdirp(self.__install_dir)
        for dep in self.__deps:
            src_dir = dep.download()
            build_dir = dep.build(src_dir)
            dep.install(build_dir)
