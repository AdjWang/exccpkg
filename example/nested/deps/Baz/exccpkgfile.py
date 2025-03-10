import logging
from multiprocessing import cpu_count
from pathlib import Path
import shutil
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from exccpkg import exccpkg, tools


class Config(exccpkg.Config):
    def __init__(self, upstream_cfg: Self | None = None) -> None:
        super().__init__(upstream_cfg)
        project_dir = Path(__file__).resolve().parents[0]
        self.project_dir = project_dir
        self.deps_dir = self.project_dir / "deps"
        self.download_dir = self.deps_dir / "download"
        self.cmake_build_type = "Release"
        self.install_dir = self.deps_dir / "out" / self.cmake_build_type

        if self.cmake_build_type == "Release":
            self.msvc_rt_lib = "MultiThreaded"
        else:
            self.msvc_rt_lib = "MultiThreadedDebug"


class GoogleTest(exccpkg.Package):
    def __init__(self) -> None:
        super().__init__(self.download, self.build, self.install)

    @staticmethod
    def download(cfg: Config) -> Path:
        url = "https://github.com/google/googletest/archive/refs/tags/v1.15.2.tar.gz"
        package_path = cfg.download_dir / "googletest-1.15.2.tar.gz"
        tools.download(url, package_path)
        shutil.unpack_archive(package_path, cfg.deps_dir)
        return cfg.deps_dir / "googletest-1.15.2"

    @staticmethod
    def build(cfg: Config, src_dir: Path) -> Path:
        build_dir = src_dir / "cmake_build" / cfg.cmake_build_type
        tools.cmake_prepare_build_dir(build_dir, rebuild=False)
        tools.run_cmd(f"""cmake -DCMAKE_BUILD_TYPE={cfg.cmake_build_type}
                                -DCMAKE_POLICY_DEFAULT_CMP0091=NEW
                                -DCMAKE_MSVC_RUNTIME_LIBRARY={cfg.msvc_rt_lib}
                                -DCMAKE_CXX_STANDARD=17
                                -DCMAKE_INSTALL_PREFIX={cfg.install_dir}
                                -DCMAKE_INSTALL_LIBDIR=lib
                                -S {src_dir} -B {build_dir}""")
        tools.run_cmd(f"""cmake --build {build_dir}
                                --config={cfg.cmake_build_type}
                                --parallel={cpu_count()}""")
        return build_dir

    @staticmethod
    def install(cfg: Config, build_dir: Path) -> None:
        tools.run_cmd(f"""cmake --install {build_dir}
                                --prefix={cfg.install_dir}""")


def resolve(cfg: Config) -> None:
    tools.mkdirp(cfg.download_dir)
    tools.mkdirp(cfg.deps_dir)
    tools.mkdirp(cfg.install_dir)
    dep_absl = GoogleTest()
    dep_absl.resolve(cfg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    resolve(cfg)
