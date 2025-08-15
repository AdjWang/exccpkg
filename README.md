# exccpkg: An explicit C++ package builder

A simple toolset dedicated to take over control C++ build-from-source pipeline by making everything explicit.

## Install

Requires `python>=3.12`

```
pip3 install exccpkg
```

> Use `python3`, `pip3` on linux and `python`, `python -m pip` on windows.

[Externally managed environment is discouraged](https://peps.python.org/pep-0668/), it is recommand to install within a virtual environment, like [uv](https://docs.astral.sh/uv/), [pipenv](https://pipenv.pypa.io/en/latest/)... Demonstration projects use pipenv.

## How to use

### Write `exccpkgfile.py`

A dummy example:

``` python
import logging
from pathlib import Path
from typing import override

from exccpkg import exccpkg, tools

class Config:
    def __init__(self) -> None:
        project_dir = Path(__file__).resolve().parents[0]
        self.project_dir = project_dir
        self.anything = "anything"


class Toolset:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def download(self, url: str, pkg_name: str, ext: str) -> Path:
        logging.info(f'Toolset download url={url} pkg_name={pkg_name} ext={ext}')
        return Path("src_dir")

    def copy(self, path: str, pkg_name: str, ext: str) -> Path:
        logging.info(f'Toolset copy path={path} pkg_name={pkg_name} ext={ext}')
        return Path("src_dir")
    
    def build(self, src_dir: Path, options: str = "") -> Path:
        logging.info(f'Toolset build src_dir={src_dir} options={options}')
        return Path("build_dir")
    
    def install(self, build_dir: Path) -> None:
        logging.info(f'Toolset install from {build_dir}')


class Context(exccpkg.Context):
    def __init__(self):
        self.cfg = Config()
        self.toolset = Toolset(self.cfg)


class PackageA(exccpkg.Package):
    name = "A"
    version = "A_version"

    @override
    def grab(self, ctx: Context) -> Path:
        url = "https://A.download"
        return ctx.toolset.download(url, "A-A_version", ".tar.gz")

    @override
    def build(self, ctx: Context, src_dir: Path) -> Path:
        return ctx.toolset.build(src_dir, "any option")

    @override
    def install(self, ctx: Context, build_dir: Path) -> None:
        return ctx.toolset.install(build_dir)


class PackageB(exccpkg.Package):
    name = "B"
    version = "B_version"

    @override
    def grab(self, ctx: Context) -> Path:
        path = "file://B.directory"
        return ctx.toolset.copy(path, "B-B_version", ".tar.gz")

    @override
    def build(self, ctx: Context, src_dir: Path) -> Path:
        return ctx.toolset.build(src_dir, "any option")

    @override
    def install(self, ctx: Context, build_dir: Path) -> None:
        return ctx.toolset.install(build_dir)


def collect() -> exccpkg.PackageCollection:
    collection = exccpkg.PackageCollection([
        PackageA(),
    ])
    # Add child dependencies, resolved former than above.
    collection.merge(exccpkg.PackageCollection([
      PackageB(),
    ]))
    return collection


def resolve(ctx: Context, collection: exccpkg.PackageCollection) -> None:
    # tools.mkdirp("any directory")
    # Override child project's configuration to ensure ABI compatibility.
    collection.resolve(ctx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Maybe useful informations to setup toolset.
    import platform
    logging.info(f'platform.system()={platform.system()}')
    from multiprocessing import cpu_count
    logging.info(f'cpu_count={cpu_count()}')

    ctx = Context()
    collection = collect()
    resolve(ctx, collection)
```

Execute script above gives result:
```
$ pipenv run python3 exccpkgfile_dummy.py 
INFO:root:platform.system()=Linux
INFO:root:cpu_count=16
INFO:root:Toolset copy path=file://B.directory pkg_name=B-B_version ext=.tar.gz
INFO:root:Toolset build src_dir=src_dir options=any option
INFO:root:Toolset install from build_dir
INFO:root:Toolset download url=https://A.download pkg_name=A-A_version ext=.tar.gz
INFO:root:Toolset build src_dir=src_dir options=any option
INFO:root:Toolset install from build_dir
```

This is how exccpkg working, it never assumes any toolset you are using, only provides common steps required by building from source -- grab, build and install. It's long, though, but developers would not change it everyday.

More comprehensive examples see `example/.../exccpkgfile.py`, supports nested local projects, proxy, grab by copy files...

Notice:

- All things that `exccpkgfile.py` do are to make something like `find_package` work, if you are using `CMake`.

- Top level project's configuration overrides nested child projects' to ensure ABI compatibility.

- Always leave a proxy entrance for parent project, i.e., do not directly call static functions inside module, for instance, `CMakeCommon.build`, use `ctx.cmake.build` which can be replaced by parent project.

- There's no default cli interface, you can build cli wrappers you like. It's fairly easy since we now have AI chatbots.

### Build dependencies

Requires ninja as default generator. Ninja is optional and set in `exccpkgfile.py`, use whatever you like.

**On windows, one MUST use [Developer Command Prompt or Developer PowerShell](https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell?view=vs-2022).** Developer console sets up compiler path as environment variable, which is essential for cmake.

```
python3 exccpkgfile.py
```

Build results output to `deps/out/[Debug/Release]`, headers in `include`, libraries in `lib`. The path is configurable in `exccpkgfile.py`, but it's recommend to stay the same among all projects otherwise the install path has to be set explicitly in `CMakeLists.txt`.

### Build project

#### CMake

On Linux:
```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=deps/out/Release -G Ninja -S . -B ./build
cmake --build ./build --config Release --target all -j $(nproc)
```

On Windows ([Developer Powershell](https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell?view=vs-2022)):
```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_DEFAULT_CMP0091=NEW -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DCMAKE_INSTALL_PREFIX=deps/out/Release -G Ninja -S . -B ./build
cmake --build ./build --config Release --target all -j $env:NUMBER_OF_PROCESSORS
```

> Use `-j $env:NUMBER_OF_PROCESSORS` on powershell, `-j %NUMBER_OF_PROCESSORS%` on cmd.

The key part is `CMAKE_INSTALL_PREFIX`, see [CMake Config Mode Search Procedure](https://cmake.org/cmake/help/latest/command/find_package.html#config-mode-search-procedure)

### Integrate with VS Code

Create [`.vscode/settings.json`](https://gist.github.com/AdjWang/17e23de3b136d2439559547fbd82e729) under project directory.

## Pros and cons

Pros

- Explicit building pipeline makes configuration issues visible.

  Sometimes it's really hard to debug some linking issues with a package manager that encapsules everything. If you never encountered those kind of issues, be cautious to use this one.

- Really easy to buildup a project with nested local projects.

- Flexible configuration.

  For instance, `https://ghproxy.link/` provides github proxy for Chinese mainland developers, as a url prefix, which is a weird way compares to normal proxy settings that modify the domain name. Exccpkg allows hooking download function to modify urls leveraging python's dynamic features.

- Easily accessible source code.

  Exccpkg puts dependency source codes within the project folder instead of a shared folder. This facilitates accessing the source code, espicially for those poor documented C/C++ projects.

Cons

  - You have to know how to write python.

  - Long configuration file.

    The tradeoff of explicit is cumbersome, since C/C++ compilers have tons of configurations, no metion to support multiple platforms.

  - Manually ABI compability control.

    Compiler configurations must be consistent between `exccpkgfile.py` and build command. If anything is broken, the compiler often failes with link errors.

  - Duplicated source code at project level.

    Exccpkg put all dependency source codes under current working project directory. Multiple projects may contain the same dependency but share nothing. For small projects, which often have dependencies no more than 30, this is not a big problem. If you really need to share some huge dependencies, directly return the folder path in `grab` function instead of copy or download.
