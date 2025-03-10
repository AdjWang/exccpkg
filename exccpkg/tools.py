# -*- coding: utf-8 -*-
import errno
import logging
import os
from pathlib import Path
import platform
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
    # Windows seems can't remove hidden directories, like .git, raising
    # "PermissionError: [WinError 5] Access is denied".
    def __rm_readonly(func, path, exc):
        excvalue = exc[1]
        if (platform.system() == "Windows" and
            excvalue.errno in (errno.EACCES, errno.ENOTEMPTY)):
            # Try platform specific commands.
            if Path(path).is_dir():
                cmd = f"rmdir /s /q {path}"
            else:
                cmd = f"del /f /q {path}"
            logging.warning(
                f"Failed to run {func} on {path}, err={excvalue} try command={cmd}")
            os.system(cmd)
        else:
            raise Exception(exc)
    if rebuild and build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=False,
                      onerror=__rm_readonly)
    mkdirp(build_dir)


def run_cmd(cmd: str) -> None:
    segments = cmd.split("\n")
    segments = [seg.strip(" ") for seg in segments]
    formatted_cmd = " ".join(segments)
    logging.debug(f"ExccPkg:{os.getcwd()}$ {formatted_cmd}")
    os.system(formatted_cmd)
