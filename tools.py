# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path
import requests
import shutil
try:
    from tqdm import tqdm
except ImportError:
    def __dummy_tqdm(iterable, total=None):
        return iterable
    tqdm = __dummy_tqdm


def mkdirp(dir: Path) -> None:
    """ Equivalent to mkdir -p <dir> """
    dir.mkdir(parents=True, exist_ok=True)


def download(url: str, file_path: Path) -> None:
    """ Download file from the url to file_path. """
    logging.info(f"Download {url} -> {file_path}")
    if file_path.exists():
        return
    resp = requests.get(url, stream=True)
    total_length = resp.headers.get('content-length')
    if total_length is not None:
        total_length = int(total_length)
    with open(file_path, "wb") as fs:
        for data in tqdm(resp.iter_content(), total=total_length):
            fs.write(data)


def cmake_prepare_build_dir(build_dir: Path, rebuild: bool = True) -> None:
    if rebuild and build_dir.exists():
        shutil.rmtree(build_dir)
    mkdirp(build_dir)


def run_cmd(cmd: str) -> None:
    segments = cmd.split("\n")
    segments = [seg.strip(" ") for seg in segments]
    formatted_cmd = " ".join(segments)
    logging.debug(f"Execute cmd={formatted_cmd}")
    os.system(formatted_cmd)
