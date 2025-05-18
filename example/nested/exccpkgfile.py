from collections import defaultdict
import logging
from multiprocessing import cpu_count
from pathlib import Path
import platform
import shutil
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import deps.Bar.exccpkgfile as deps_bar
import deps.Baz.exccpkgfile as deps_baz
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
        self.generator = "Ninja"

        # sanitizer = "-fsanitize=thread"
        sanitizer = ""
        CFLAGS = defaultdict(dict)
        CXXFLAGS = defaultdict(dict)
        LDFLAGS = defaultdict(dict)
        CFLAGS["Linux"]["Debug"] = f"-fdata-sections -ffunction-sections {sanitizer} -fno-omit-frame-pointer -g"
        CFLAGS["Linux"]["Release"] = "-fdata-sections -ffunction-sections -fno-omit-frame-pointer -g -Wno-error=deprecated-declarations"
        CXXFLAGS["Linux"]["Debug"] = f"-fdata-sections -ffunction-sections {sanitizer} -fno-omit-frame-pointer -g"
        CXXFLAGS["Linux"]["Release"] = "-fdata-sections -ffunction-sections -fno-omit-frame-pointer -g -Wno-error=deprecated-declarations"
        LDFLAGS["Linux"]["Debug"] = "-Wl,--gc-sections"
        LDFLAGS["Linux"]["Release"] = "-Wl,--gc-sections"
        CFLAGS["Windows"]["Debug"] = "/MP /utf-8 /EHsc"
        CFLAGS["Windows"]["Release"] = "/MP /utf-8 /Gy /EHsc"
        CXXFLAGS["Windows"]["Debug"] = "/MP /utf-8 /EHsc"
        CXXFLAGS["Windows"]["Release"] = "/MP /utf-8 /Gy /EHsc"
        LDFLAGS["Windows"]["Debug"] = "/OPT:REF /INCREMENTAL:NO"
        LDFLAGS["Windows"]["Release"] = "/OPT:REF /INCREMENTAL:NO"

        if self.cmake_build_type == "Release":
            self.msvc_rt_lib = "MultiThreaded"
        else:
            self.msvc_rt_lib = "MultiThreadedDebug"

        # Use policy CMP0091 with CMAKE_MSVC_RUNTIME_LIBRARY
        # See: https://cmake.org/cmake/help/latest/policy/CMP0091.html
        self.cmake_common = f"""
            -DCMAKE_BUILD_TYPE={self.cmake_build_type}
            -DCMAKE_CXX_STANDARD=23
            -DCMAKE_POLICY_DEFAULT_CMP0091=NEW
            -DCMAKE_MSVC_RUNTIME_LIBRARY={self.msvc_rt_lib}
            -DCMAKE_INSTALL_PREFIX={self.install_dir}
            -DCMAKE_INSTALL_LIBDIR=lib """
        if platform.system() == "Linux":
            os.environ["CFLAGS"] = CFLAGS["Linux"][self.cmake_build_type]
            os.environ["CXXFLAGS"] = CXXFLAGS["Linux"][self.cmake_build_type]
            os.environ["LDFLAGS"] = LDFLAGS["Linux"][self.cmake_build_type]
        elif platform.system() == "Windows":
            self.cmake_common += f'-DCMAKE_C_FLAGS="{CFLAGS["Windows"][self.cmake_build_type]} "'
            self.cmake_common += f'-DCMAKE_CXX_FLAGS="{CXXFLAGS["Windows"][self.cmake_build_type]} "'
            self.cmake_common += f'-DCMAKE_LINK_FLAGS="{LDFLAGS["Windows"][self.cmake_build_type]} "'

        self.rebuild = False


class CMakeCommon:
    @staticmethod
    def download(cfg: Config, url: str, pkg_name: str, ext: str) -> Path:
        package_path = cfg.download_dir / f"{pkg_name}{ext}"
        tools.download(url, package_path)
        shutil.unpack_archive(package_path, cfg.deps_dir)
        return cfg.deps_dir / pkg_name
    
    @staticmethod
    def build(cfg: Config, src_dir: Path, cmake_options: str = "") -> Path:
        build_dir = src_dir / "cmake_build" / cfg.cmake_build_type
        tools.cmake_prepare_build_dir(build_dir, rebuild=cfg.rebuild)
        tools.run_cmd(f"""cmake {cfg.cmake_common} {cmake_options}
                                -G {cfg.generator} -S {src_dir}
                                -B {build_dir}""")
        tools.run_cmd(f"""cmake --build {build_dir}
                                --config={cfg.cmake_build_type}
                                --parallel={cpu_count()}""")
        return build_dir
    
    @staticmethod
    def install(cfg: Config, build_dir: Path) -> None:
        tools.run_cmd(f"""cmake --install {build_dir}
                                --prefix={cfg.install_dir}""")


class AbseilCpp(exccpkg.Package):
    def __init__(self) -> None:
        super().__init__(self.download, self.build, CMakeCommon.install)

    @staticmethod
    def download(cfg: Config) -> Path:
        url = "https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz"
        return CMakeCommon.download(cfg, url, "abseil-cpp-20240722.0", ".tar.gz")

    @staticmethod
    def build(cfg: Config, src_dir: Path) -> Path:
        return CMakeCommon.build(cfg, src_dir, "-DABSL_MSVC_STATIC_RUNTIME=ON")


def resolve(cfg: Config) -> None:
    tools.mkdirp(cfg.download_dir)
    tools.mkdirp(cfg.deps_dir)
    tools.mkdirp(cfg.install_dir)
    # Override child project's configuration to ensure ABI compatibility.
    deps_bar.resolve(cfg)
    deps_baz.resolve(cfg)
    deps = [
        AbseilCpp(),
        # ...
    ]
    for dep in deps:
        dep.resolve(cfg)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    resolve(cfg)
