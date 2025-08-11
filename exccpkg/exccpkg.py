# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from collections import Counter
import inspect
import logging
from pathlib import Path
from typing import Callable, Dict, List
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Context:
    """ Add anything you need, then passed to resolve. """
    def __init__(self) -> None:
        ...


class Package(ABC):
    def __init__(self) -> None:
        """
        Args:
            name: Package name, used to identify duplications.
            version: Package version, used to identify duplications.
        """
        assert(hasattr(self, "name"))
        assert(hasattr(self, "version"))

    @abstractmethod
    def grab(self, ctx: Context) -> Path:
        """ Grab package source files. Input context, return package source path. """
        ...

    @abstractmethod
    def build(self, ctx: Context, src_dir: Path) -> Path:
        """ Build package. Input context and source path, return build path. """
        ...

    @abstractmethod
    def install(self, ctx: Context, build_dir: Path) -> None:
        """ Install package. Input context and build path. """
        ...

    def resolve(self, ctx: Context) -> None:
        """ Run grag, build and install in order. """
        src_dir = self.grab(ctx)
        build_dir = self.build(ctx, src_dir)
        self.install(ctx, build_dir)


class PackageCollection:
    def __init__(self, deps: List[Package]) -> None:
        self.__deps = deps

    def merge(self, collection: Self) -> None:
        self.__deps.extend(collection.__deps)
    
    def resolve(self, ctx: Context) -> None:
        no_dup_deps = self.__drop_duplicates()
        for dep in no_dup_deps:
            dep.resolve(ctx)

    def __find_duplicate_deps(self) -> Dict[str, List[int]]:
        names = [dep.name for dep in self.__deps]
        counts = Counter(names)
        duplicate_names = [item for item, count in counts.items() if count > 1]
        name_indices: Dict[str, List[int]] = {}
        for dup_name in duplicate_names:
            indices = [idx for idx, name in enumerate(names) if name == dup_name]
            name_indices[dup_name] = indices
        return name_indices

    def __drop_duplicates(self) -> List[Package]:
        vers = [dep.version for dep in self.__deps]
        pkginfos = [
            f'{inspect.getsourcefile(dep.__class__)}:{inspect.getsourcelines(dep.__class__)[1]}'
            for dep in self.__deps
        ]
        # Check version conflictions.
        dup_deps = self.__find_duplicate_deps()
        for dup_dep_name, dep_indices in dup_deps.items():
            dep_vers = [vers[i] for i in dep_indices]
            dep_infos = [pkginfos[i] for i in dep_indices]
            if len(set(dep_vers)) > 1:
                logging.error("Version confliction:")
                logging.error(f"Package name: {dup_dep_name}")
                logging.error(f"Package versions: {dep_vers}")
                logging.error(f"Package sources:")
                for info in dep_infos:
                    logging.error(info)
                raise Exception(f'Version confliction')
            else:
                logging.debug(f"Find duplications name={dup_dep_name} vers={dep_vers} infos={dep_infos}")
        # Drop duplications.
        self.__deps_dict: Dict[str, Package] = dict()
        for dep in self.__deps:
            self.__deps_dict[f"{dep.name}-{dep.version}"] = dep
        no_dup_deps = list(self.__deps_dict.values())
        # Output in alpha order.
        no_dup_deps = sorted(no_dup_deps, key=lambda x: x.name)
        logging.debug(f"Packages={[f"{dep.name}-{dep.version}" for dep in no_dup_deps]}")
        return no_dup_deps
