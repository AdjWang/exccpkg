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

Examples see `example/.../exccpkgfile.py`, supports nested local projects, proxy, grab by copy files...

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
