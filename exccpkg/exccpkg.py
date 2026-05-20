# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
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
    def __init__(self, pkgs: List[Package]) -> None:
        self.__depth = 0
        # Packages of current module.
        self.__pkgs: List[Package] = pkgs
        self.__sub_collections: List[PackageCollection] = []

    def add_submodule(
        self, ctx: Context, submodule: Package, exccpkgfilepath: str = "exccpkgfile.py"
    ) -> None:
        """ Add submodule. """
        src_dir = submodule.grab(ctx)
        submodule_name = getattr(submodule, "name")
        submodule_path = Path(src_dir) / exccpkgfilepath
        sub_pkg = self.__import_from_path(submodule_name, submodule_path)
        sub_collection = sub_pkg.collect(ctx)
        self.add_dependency_collection(sub_collection)

    def add_dependency_collection(self, collection: Self) -> None:
        """ Add packages with larger depth. """
        self.__sub_collections.append(collection)

    def resolve(self, ctx: Context) -> List[Package]:
        # Resulve dependency map.
        self.__check_conflictions()
        self.__set_depth(self.__depth)
        depth_pkgs: List[Tuple[int, Package]] = self.__filter_pkgs()
        logging.debug(f"Resolved pkgs={[(pkg[0], self.__pkg_id(pkg[1])) for pkg in depth_pkgs]}")
        pkgs = [pkg[1] for pkg in depth_pkgs]
        # Grab, build and install.
        src_dirs = [pkg.grab(ctx) for pkg in pkgs]
        for pkg, src_dir in zip(pkgs, src_dirs):
            build_dir = pkg.build(ctx, src_dir)
            pkg.install(ctx, build_dir)
        return pkgs

    @staticmethod
    def __pkg_id(pkg: Package) -> str:
        return f"{getattr(pkg, "name")}-{getattr(pkg, "version")}"

    def __set_depth(self, depth: int) -> None:
        self.__depth = depth
        for collection in self.__sub_collections:
            collection.__set_depth(depth + 1)

    def __filter_pkgs(self) -> List[Tuple[int, Package]]:
        """Drop duplications and get max depth."""
        # Get all packages.
        # Dict[id, Tuple[depth, Package]]
        id_depth_pkgs: Dict[str, Tuple[int, Package]] = dict()
        for pkg in self.__pkgs:
            id_depth_pkgs[self.__pkg_id(pkg)] = (self.__depth, pkg)
        for collection in self.__sub_collections:
            for (depth, pkg) in collection.__filter_pkgs():
                id = self.__pkg_id(pkg)
                if id in id_depth_pkgs:
                    id_depth_pkgs[id] = (max(depth, id_depth_pkgs[id][0]), pkg)
                else:
                    id_depth_pkgs[id] = (depth, pkg)
        pkgs_sorted: List[Tuple[int, Package]] = list(id_depth_pkgs.values())
        pkgs_sorted = sorted(pkgs_sorted, key=lambda x: x[0], reverse=True)
        return pkgs_sorted

    def __check_conflictions(self) -> None:
        """ Check if there are packages with same name but different versions. """
        # Get all packages.
        pkgs: List[Package] = self.__pkgs
        for collection in self.__sub_collections:
            pkgs.extend(collection.__pkgs)
        names = [getattr(pkg, "name") for pkg in pkgs]
        vers = [getattr(pkg, "version") for pkg in pkgs]
        infos = [
            f"{inspect.getsourcefile(pkg.__class__)}:{inspect.getsourcelines(pkg.__class__)[1]}"
            for pkg in pkgs
        ]
        # Check version conflictions.
        # Dict[name, Dict[vers, info]]
        dup_deps: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for i in range(len(pkgs)):
            dup_deps[names[i]].append((vers[i], infos[i]))
        for name, dups in dup_deps.items():
            ver_count = len(set([dup[0] for dup in dups]))
            if ver_count > 1:
                logging.error("Version confliction:")
                logging.error(f"Package name: {name}")
                logging.error(f"Package versions: {dups}")
                raise Exception(f'Version confliction')
            elif ver_count == 1 and len(dups) > 1:
                logging.debug(f"Found duplicates name={name} vers={dups}")

    @staticmethod
    def __import_from_path(module_name, file_path):
        logging.debug(f'loading module={module_name} at={file_path}')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
