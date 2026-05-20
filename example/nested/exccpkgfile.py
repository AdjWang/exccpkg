from collections import defaultdict
import logging
from multiprocessing import cpu_count
import os
from pathlib import Path
import platform
from typing import override

from exccpkg import exccpkg, tools

PROJ_DIR = Path(__file__).parent.resolve()
DEPS_DIR = (PROJ_DIR / "deps").resolve()


class Config:
    def __init__(self) -> None:
        project_dir = Path(__file__).resolve().parents[0]
        self.project_dir = project_dir
        self.deps_dir = self.project_dir / "deps"
        self.download_dir = self.deps_dir / "download"
        self.cmake_build_type = "Release"
        self.install_dir = self.deps_dir / "out" / self.cmake_build_type
        self.generator = "Ninja"

        self.sanitizer = "none"
        if self.sanitizer == "address":
            cxx_sanitizer = "-fsanitize=address"
            ld_sanitizer = "-lasan"
        elif self.sanitizer == "thread":
            cxx_sanitizer = "-fsanitize=thread"
            ld_sanitizer = "-ltsan"
        else:
            cxx_sanitizer = ""
            ld_sanitizer = ""
        CFLAGS = defaultdict(dict)
        CXXFLAGS = defaultdict(dict)
        LDFLAGS = defaultdict(dict)
        CFLAGS["Linux"]["Debug"] = f"-fdata-sections -ffunction-sections {cxx_sanitizer} -fno-omit-frame-pointer -g"
        CFLAGS["Linux"]["Release"] = "-fdata-sections -ffunction-sections -fno-omit-frame-pointer -g -Wno-error=deprecated-declarations"
        CXXFLAGS["Linux"]["Debug"] = f"-fdata-sections -ffunction-sections {cxx_sanitizer} -fno-omit-frame-pointer -g"
        CXXFLAGS["Linux"]["Release"] = "-fdata-sections -ffunction-sections -fno-omit-frame-pointer -g -Wno-error=deprecated-declarations"
        LDFLAGS["Linux"]["Debug"] = f"-Wl,--gc-sections {ld_sanitizer}"
        LDFLAGS["Linux"]["Release"] = f"-Wl,--gc-sections {ld_sanitizer}"
        CFLAGS["Windows"]["Debug"] = "/MP /utf-8 /EHsc"
        CFLAGS["Windows"]["Release"] = "/MP /utf-8 /Gy /EHsc"
        CXXFLAGS["Windows"]["Debug"] = "/MP /utf-8 /EHsc"
        CXXFLAGS["Windows"]["Release"] = "/MP /utf-8 /Gy /EHsc"
        LDFLAGS["Windows"]["Debug"] = "/OPT:REF /INCREMENTAL:NO"
        LDFLAGS["Windows"]["Release"] = "/OPT:REF /INCREMENTAL:NO"

        self.cmake_common = f"""
            -DCMAKE_BUILD_TYPE={self.cmake_build_type}
            -DCMAKE_CXX_STANDARD=23
            -DCMAKE_INSTALL_PREFIX={self.install_dir}
            -DCMAKE_INSTALL_LIBDIR=lib
            -DCMAKE_POLICY_VERSION_MINIMUM=3.5 """
        if platform.system() == "Linux":
            os.environ["CFLAGS"] = CFLAGS["Linux"][self.cmake_build_type]
            os.environ["CXXFLAGS"] = CXXFLAGS["Linux"][self.cmake_build_type]
            os.environ["LDFLAGS"] = LDFLAGS["Linux"][self.cmake_build_type]
        elif platform.system() == "Windows":
            if self.cmake_build_type == "Release":
                self.msvc_rt_lib = "MultiThreaded"
            else:
                self.msvc_rt_lib = "MultiThreadedDebug"
            # Use policy CMP0091 with CMAKE_MSVC_RUNTIME_LIBRARY
            # See: https://cmake.org/cmake/help/latest/policy/CMP0091.html
            self.cmake_common += f'-DCMAKE_POLICY_DEFAULT_CMP0091=NEW -DCMAKE_MSVC_RUNTIME_LIBRARY={self.msvc_rt_lib} '
            self.cmake_common += f'-DCMAKE_C_FLAGS="{CFLAGS["Windows"][self.cmake_build_type]} "'
            self.cmake_common += f'-DCMAKE_CXX_FLAGS="{CXXFLAGS["Windows"][self.cmake_build_type]} "'
            self.cmake_common += f'-DCMAKE_LINK_FLAGS="{LDFLAGS["Windows"][self.cmake_build_type]} "'

        self.dryrun = False
        self.rebuild = False


class CMakeCommon:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def download(self, url: str, pkg_name: str, ext: str, unpack_dir: str = "") -> Path:
        package_path = self.cfg.download_dir / f"{pkg_name}{ext}"
        src_path = self.cfg.deps_dir / pkg_name
        tools.download(url, package_path, self.cfg.dryrun)
        if unpack_dir == "":
            tools.unpack(package_path, self.cfg.deps_dir, self.cfg.dryrun)
        else:
            tools.unpack(package_path, self.cfg.deps_dir / unpack_dir, self.cfg.dryrun)
        return src_path
    
    def build(self, src_dir: Path, cmake_options: str = "") -> Path:
        build_dir = src_dir / "cmake_build" / self.cfg.cmake_build_type
        tools.cmake_prepare_build_dir(build_dir, rebuild=self.cfg.rebuild, dryrun=self.cfg.dryrun)
        tools.run_cmd(f"""cmake {self.cfg.cmake_common} {cmake_options}
                                -G "{self.cfg.generator}" -S {src_dir}
                                -B {build_dir}""", self.cfg.dryrun)
        tools.run_cmd(f"""cmake --build {build_dir}
                                --config={self.cfg.cmake_build_type}
                                --parallel={cpu_count()}""", self.cfg.dryrun)
        return build_dir
    
    def install(self, build_dir: Path) -> None:
        tools.run_cmd(f"""cmake --install {build_dir}
                                --config={self.cfg.cmake_build_type}
                                --prefix={self.cfg.install_dir}""", self.cfg.dryrun)


class Context(exccpkg.Context):
    def __init__(self):
        self.cfg = Config()
        self.cmake = CMakeCommon(self.cfg)


class AbseilCpp(exccpkg.Package):
    name = "abseil-cpp"
    version = "20240722.0"

    @override
    def grab(self, ctx: Context) -> Path:
        url = "https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz"
        return ctx.cmake.download(url, "abseil-cpp-20240722.0", ".tar.gz")

    @override
    def build(self, ctx: Context, src_dir: Path) -> Path:
        return ctx.cmake.build(src_dir, "-DABSL_MSVC_STATIC_RUNTIME=ON")

    @override
    def install(self, ctx: Context, build_dir: Path) -> None:
        return ctx.cmake.install(build_dir)


class Bar(exccpkg.Package):
    name = "Bar"
    version = "v0.0.0"

    @override
    def grab(self, ctx: Context) -> Path:
        return DEPS_DIR / "Bar"

    @override
    def build(self, ctx: Context, src_dir: Path) -> Path:
        return ctx.cmake.build(src_dir)

    @override
    def install(self, ctx: Context, build_dir: Path) -> None:
        return ctx.cmake.install(build_dir)


class Baz(exccpkg.Package):
    name = "Baz"
    version = "v0.0.0"

    @override
    def grab(self, ctx: Context) -> Path:
        return DEPS_DIR / "Baz"

    @override
    def build(self, ctx: Context, src_dir: Path) -> Path:
        return ctx.cmake.build(src_dir)

    @override
    def install(self, ctx: Context, build_dir: Path) -> None:
        return ctx.cmake.install(build_dir)


def collect(ctx: Context) -> exccpkg.PackageCollection:
    collection = exccpkg.PackageCollection([
        AbseilCpp(),
        # ...
    ])
    # Execute grab and collect recursively to get submodule's submodules.
    # Submodule resolved first.
    collection.add_submodule(ctx, Bar())
    collection.add_submodule(ctx, Baz())
    return collection


def resolve(ctx: Context, collection: exccpkg.PackageCollection) -> None:
    tools.mkdirp(ctx.cfg.download_dir)
    tools.mkdirp(ctx.cfg.deps_dir)
    tools.mkdirp(ctx.cfg.install_dir)
    # Override child project's configuration to ensure ABI compatibility.
    collection.resolve(ctx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ctx = Context()
    collection = collect(ctx)
    resolve(ctx, collection)
