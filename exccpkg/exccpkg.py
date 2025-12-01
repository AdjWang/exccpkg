# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from collections import Counter
import importlib.util
import inspect
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple
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
    def grab(self, ctx: Any) -> Path:
        """ Grab package source files. Input context, return package source path. """
        ...

    @abstractmethod
    def build(self, ctx: Any, src_dir: Path) -> Path:
        """ Build package. Input context and source path, return build path. """
        ...

    @abstractmethod
    def install(self, ctx: Any, build_dir: Path) -> None:
        """ Install package. Input context and build path. """
        ...

    def resolve(self, ctx: Any) -> None:
        """ Run grag, build and install in order. """
        src_dir = self.grab(ctx)
        build_dir = self.build(ctx, src_dir)
        self.install(ctx, build_dir)


class PackageCollection:
    def __init__(self, deps: List[Package]) -> None:
        # Packages of current module.
        self.__deps = deps
        self.__deps_depth: Dict[str, Tuple[int, Package]] = dict()
        for dep in self.__deps:
            self.__deps_depth[self.__pkg_id(dep)] = (0, dep)
        # Pending packages that resolved after downloading current packages.
        self.__pending_pkgs: List[str] = []

    def add_package(self, exccpkg_module: str) -> None:
        """
        Add packages from path.

        Merging subpackages requires them had been downloadad to check
        exccpkgfile, therefore needs input as path before downloading
        instead of a python module.
        """
        self.__pending_pkgs.append(exccpkg_module)

    def merge(self, collection: Self) -> None:
        """ Merge packages from child projects with larger depth. """
        self.__deps.extend(collection.__deps)
        for id, dep in collection.__deps_depth.items():
            self.__deps_depth[id] = (dep[0] + 1, dep[1])
        self.__pending_pkgs.extend(collection.__pending_pkgs)

    def resolve(self, ctx: Context) -> None:
        grab_cache: Dict[str, Path] = dict()
        # Recursively add sub package directories.
        while len(self.__pending_pkgs) > 0:
            # Download first.
            no_dup_deps = self.__drop_duplicates()
            for dep in no_dup_deps:
                if self.__pkg_id(dep) not in grab_cache:
                    src_dir = dep.grab(ctx)
                    grab_cache[self.__pkg_id(dep)] = src_dir
            # Import sub packages.
            pending_pkgs = self.__pending_pkgs
            self.__pending_pkgs = []
            for sub_pkg_path in pending_pkgs:
                logging.debug(f'loading module={sub_pkg_path}')
                sub_pkg = importlib.import_module(sub_pkg_path)
                sub_collection = sub_pkg.collect()
                self.merge(sub_collection)
        # All nested packages are resolved, try to drop duplications and add
        # rests.
        no_dup_deps = self.__drop_duplicates()
        src_dirs = []
        for dep in no_dup_deps:
            if self.__pkg_id(dep) in grab_cache:
                src_dirs.append(grab_cache[self.__pkg_id(dep)])
            else:
                src_dirs.append(dep.grab(ctx))
        # Build and install.
        for dep, src_dir in zip(no_dup_deps, src_dirs):
            build_dir = dep.build(ctx, src_dir)
            dep.install(ctx, build_dir)

    def __pkg_id(self, pkg: Package) -> str:
        return f"{pkg.name}-{pkg.version}"

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
        no_dup_deps: List[Tuple[int, Package]] = list(self.__deps_depth.values())
        # Output in depth decending order.
        no_dup_deps = sorted(no_dup_deps, key=lambda x: x[0])
        output_deps = [dep[1] for dep in reversed(no_dup_deps)]
        logging.debug(f"Packages={[f"{dep.name}-{dep.version}" for dep in output_deps]}")
        return output_deps
