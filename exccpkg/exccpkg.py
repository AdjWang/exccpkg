# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Callable
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Config:
    def __init_subclass__(cls, **kwargs) -> None:
        """ Call upstream.config_downstream(self) after self.__init__() """
        super().__init_subclass__(**kwargs)

        def __wrap_init(init):
            def __wrapped_init(self, upstream_cfg: Self | None = None):
                init(self, upstream_cfg)
                if isinstance(self, cls) and upstream_cfg is not None:
                    upstream_cfg.config_downstream(self)
            return __wrapped_init
        cls.__init__ = __wrap_init(cls.__init__)

    def __init__(self, upstream_cfg: Self | None = None) -> None:
        ...

    def config_downstream(self, downstream_cfg: Self) -> None:
        """ May get or set depencence configurations here. """
        ...


class Package:
    def __init__(self, grab: Callable[[Config], Path],
                 build: Callable[[Config, Path], Path],
                 install: Callable[[Config, Path], None]) -> None:
        self.grab = grab
        self.build = build
        self.install = install

    def resolve(self, cfg: Config) -> None:
        src_dir = self.grab(cfg)
        build_dir = self.build(cfg, src_dir)
        self.install(cfg, build_dir)
