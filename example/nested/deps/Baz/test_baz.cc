#include <string>
#include <vector>

#include "gmock/gmock.h"
using ::testing::ElementsAre;

TEST(Baz, basic) {
  std::vector<std::string> v = {"foo","bar","baz"};
  EXPECT_THAT(v, ElementsAre("foo", "bar", "baz"));
}
