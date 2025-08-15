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
        url = "https://B.download"
        return ctx.toolset.download(url, "B-B_version", ".tar.gz")

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
