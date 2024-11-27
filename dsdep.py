# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
from multiprocessing import cpu_count
import os
from pathlib import Path
import requests
import shutil
import sys
import tarfile
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x
from typing import Callable


PROJECT_DIR = Path(sys.argv[0]).parent.parent.resolve()
DEPS_DIR = PROJECT_DIR / "deps"
DOWNLOAD_DIR = DEPS_DIR / "download"
INSTALL_DIR = DEPS_DIR / "out"


def mkdirp(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_download_filepath(file_name: Path) -> Path:
    file_path = DOWNLOAD_DIR / file_name
    return file_path


def get_source_dir(extract_dir: Path) -> Path:
    source_dir = DEPS_DIR / extract_dir
    return source_dir


def download(file_path: Path, url: str) -> None:
    logging.info(f"Download {url} -> {file_path}")
    if file_path.exists():
        return
    resp = requests.get(url, stream=True)
    with open(file_path, "wb") as fs:
        for data in tqdm(resp.iter_content()):
            fs.write(data)


def extract_targz(file_path: Path, output_path: Path) -> None:
    with tarfile.open(file_path) as f:
        f.extractall(output_path)


@dataclass
class DepInfo:
    url: str
    # where the file name without extension is the extract directory name
    download_file: Path
    extract_dir: Path
    build_source: Callable[[Path], None]


def build_dep(source_dir: Path, build_source: Callable[[Path], None],
              rebuild: bool = True) -> None:
    build_dir = source_dir / "build"
    if rebuild and build_dir.exists():
        shutil.rmtree(build_dir)
    mkdirp(build_dir)
    build_source(build_dir)


if __name__ == "__main__":
    CMAKE_BUILD_TYPE = "Release"
    CMAKE_MODULE_DIR = INSTALL_DIR / "lib/cmake"

    # TODO: move to user configure py
    def __build_absl(build_dir: Path) -> None:
        os.chdir(build_dir.parent)
        cmd_config = f"""cmake -B {build_dir}
            -DCMAKE_BUILD_TYPE={CMAKE_BUILD_TYPE}
            -DCMAKE_CXX_STANDARD=17
            -DCMAKE_INSTALL_PREFIX={INSTALL_DIR}
            -DCMAKE_INSTALL_LIBDIR=lib"""
        cmd_build = f"""cmake --build {build_dir} --config={CMAKE_BUILD_TYPE} -j={cpu_count()}"""
        cmd_install = f"""cmake --install {build_dir} --prefix={INSTALL_DIR}"""
        os.system(cmd_config)
        os.system(cmd_build)
        os.system(cmd_install)

    logging.basicConfig(level=logging.INFO)
    mkdirp(DEPS_DIR)
    mkdirp(DOWNLOAD_DIR)
    mkdirp(INSTALL_DIR)
    deps = [
        DepInfo(url="https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz",
                download_file="abseil-cpp-20240722.0.tar.gz",
                extract_dir="abseil-cpp-20240722.0",
                build_source=__build_absl),
    ]
    for dep in deps:
        file_path = get_download_filepath(dep.download_file)
        download(file_path, dep.url)
        extract_targz(file_path, DEPS_DIR)
        source_dir = get_source_dir(dep.extract_dir)
        build_dep(source_dir, dep.build_source, rebuild=False)
