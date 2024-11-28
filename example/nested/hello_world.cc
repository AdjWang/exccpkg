// https://abseil.io/docs/cpp/quickstart-cmake
#include <iostream>
#include <string>
#include <vector>
#include "absl/strings/str_join.h"

extern void PrintBar();

int main() {
  std::vector<std::string> v = {"foo","bar","baz"};
  std::string s = absl::StrJoin(v, "-");

  std::cout << "Foo: Joined string: " << s << "\n";
  PrintBar();
  return 0;
}
