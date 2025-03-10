# exccpkg: An explicit C++ package builder

## Build project

### CMake

```
cmake -B build -G Ninja -DCMAKE_PREFIX_PATH=deps/out/Release -DCMAKE_BUILD_TYPE=Release
cmake --build ./build --config=Release
```

### Makefile
