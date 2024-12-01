// https://abseil.io/docs/cpp/quickstart-cmake
#include <iostream>
#include <string>
#include <vector>
#include "absl/strings/str_join.h"

void PrintBar() {
  std::vector<std::string> v = {"foo","bar","baz"};
  std::string s = absl::StrJoin(v, "-");

  std::cout << "Bar: Joined string: " << s << "\n";
}
