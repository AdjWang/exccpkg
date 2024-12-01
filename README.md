# DSPkg: A dead simple C++ package manager

dspkg choose to let it go.

## Build project

### CMake

```
cmake -B build -G Ninja -DCMAKE_PREFIX_PATH=deps/out -DCMAKE_BUILD_TYPE=Release
cmake --build ./build --config=Release
```

### Makefile
