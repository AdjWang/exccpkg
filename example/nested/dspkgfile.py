import logging
from multiprocessing import cpu_count
from pathlib import Path
import shutil
import sys

from dspkg import dspkg, tools
import deps.Bar.dspkgfile as deps_bar

PROJECT_DIR = Path(sys.argv[0]).resolve().parents[0]
DEPS_DIR = PROJECT_DIR / "deps"
DOWNLOAD_DIR = DEPS_DIR / "download"
INSTALL_DIR = DEPS_DIR / "out"

CMAKE_BUILD_TYPE = "Release"
CMAKE_MODULE_DIR = INSTALL_DIR / "lib/cmake"

logging.basicConfig(level=logging.INFO)

# abseil-cpp
def download_absl() -> Path:
    url = "https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz"
    package_path = DOWNLOAD_DIR / "abseil-cpp-20240722.0.tar.gz"
    tools.download(url, package_path)
    shutil.unpack_archive(package_path, DEPS_DIR)
    return DEPS_DIR / "abseil-cpp-20240722.0"

def build_absl(src_dir: Path) -> Path:
    build_dir = src_dir / "build"
    tools.cmake_prepare_build_dir(build_dir, rebuild=False)
    tools.run_cmd(f"""cmake
        -DCMAKE_BUILD_TYPE={CMAKE_BUILD_TYPE}
        -DCMAKE_CXX_STANDARD=17
        -DCMAKE_INSTALL_PREFIX={INSTALL_DIR}
        -DCMAKE_INSTALL_LIBDIR=lib
        -S {src_dir} -B {build_dir}""")
    tools.run_cmd(f"""cmake --build {build_dir} --config={CMAKE_BUILD_TYPE} -j={cpu_count()}""")
    return build_dir

def install_absl(build_dir: Path) -> None:
    tools.run_cmd(f"""cmake --install {build_dir} --prefix={INSTALL_DIR}""")


def resolve():
    pkgs = dspkg.DsPkg(DOWNLOAD_DIR, DEPS_DIR, INSTALL_DIR)
    pkgs.add_dep(dspkg.DepInfo(download=download_absl, build=build_absl, install=install_absl))
    pkgs.resolve()

if __name__ == "__main__":
    deps_bar.resolve()
    resolve()
