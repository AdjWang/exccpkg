import logging
from multiprocessing import cpu_count
from pathlib import Path
import shutil
from typing import Self

# Set proxy by python black magic :)
# Would also apply to dependencies that using tool.download
from urllib.parse import urlparse
raw_download = tools.download
def download(url: str, file_path: Path) -> None:
    o = urlparse(url)
    if o.hostname == "github.com":
        # For machines reside in Chinese mainland.
        url = "https://www.ghproxy.cn/" + url
    raw_download(url, file_path)
tools.download = download

from dspkg import dspkg, tools


class Config(dspkg.Config):
    def __init__(self, upstream_cfg: Self | None = None) -> None:
        super().__init__(upstream_cfg)
        project_dir = Path(__file__).resolve().parents[0]
        self.project_dir = project_dir
        self.deps_dir = self.project_dir / "deps"
        self.download_dir = self.deps_dir / "download"
        self.cmake_build_type = "Release"
        self.install_dir = self.deps_dir / "out" / self.cmake_build_type


class AbseilCpp(dspkg.Package):
    def __init__(self) -> None:
        super().__init__(self.download_absl, self.build_absl, self.install_absl)

    @staticmethod
    def download_absl(cfg: Config) -> Path:
        url = "https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz"
        package_path = cfg.download_dir / "abseil-cpp-20240722.0.tar.gz"
        tools.download(url, package_path)
        shutil.unpack_archive(package_path, cfg.deps_dir)
        return cfg.deps_dir / "abseil-cpp-20240722.0"

    @staticmethod
    def build_absl(cfg: Config, src_dir: Path) -> Path:
        build_dir = src_dir / "cmake_build" / cfg.cmake_build_type
        tools.cmake_prepare_build_dir(build_dir, rebuild=False)
        tools.run_cmd(f"""cmake -DCMAKE_BUILD_TYPE={cfg.cmake_build_type}
                                -DCMAKE_CXX_STANDARD=17
                                -DCMAKE_INSTALL_PREFIX={cfg.install_dir}
                                -DCMAKE_INSTALL_LIBDIR=lib
                                -S {src_dir} -B {build_dir}""")
        tools.run_cmd(f"""cmake --build {build_dir}
                                --config={cfg.cmake_build_type}
                                --parallel={cpu_count()}""")
        return build_dir

    @staticmethod
    def install_absl(cfg: Config, build_dir: Path) -> None:
        tools.run_cmd(f"""cmake --install {build_dir}
                                --prefix={cfg.install_dir}""")


def resolve(cfg: Config) -> None:
    tools.mkdirp(cfg.download_dir)
    tools.mkdirp(cfg.deps_dir)
    tools.mkdirp(cfg.install_dir)
    dep_absl = AbseilCpp()
    dep_absl.resolve(cfg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    resolve(cfg)
