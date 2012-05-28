// Copyright 2010-2012, Google Inc.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//     * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//     * Neither the name of Google Inc. nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include <string>
#include <vector>
#include "base/file_stream.h"
#include "base/singleton.h"
#include "base/util.h"
#include "converter/connector.h"
#include "converter/test_connector.h"
#include "testing/base/public/gunit.h"

DECLARE_string(test_srcdir);

namespace mozc {

namespace {

bool ParseLine(const string &line, uint16 *rid, uint16 *lid, int *cost) {
  DCHECK(rid);
  DCHECK(lid);
  DCHECK(cost);
  vector<string> tokens;
  Util::SplitStringUsing(line, " ", &tokens);
  if (tokens.size() != 3) {
    return false;
  }

  *rid = atoi32(tokens[0].c_str());
  *lid = atoi32(tokens[1].c_str());
  *cost = atoi32(tokens[2].c_str());
  return true;
}

// Get actual file path for testing
string GetFilePath(const string &path) {
  return Util::JoinPath(FLAGS_test_srcdir, path);
}
}  // namespace

class TestConnectorTest : public testing::Test {
 protected:
  TestConnectorTest() : connector_(Singleton<Connector>::get()),
                        test_connector_(Singleton<TestConnector>::get()),
                        data_file_(GetFilePath(
                            "data/dictionary/connection.txt")),
                        test_file_(GetFilePath(
                            "data/test/dictionary/connection.txt")) {}

  const Connector *connector_;
  const TestConnector *test_connector_;
  const string data_file_;
  const string test_file_;
};

TEST_F(TestConnectorTest, RandomValueCheck) {
  InputFileStream ifs(test_file_.c_str());
  EXPECT_TRUE(ifs != NULL);
  string header_line;
  EXPECT_TRUE(getline(ifs, header_line));

  string line;
  uint16 rid, lid;
  int cost;
  while (getline(ifs, line)) {
    // connection data have several millions of entries
    if (Util::Random(100000) != 0) {
      continue;
    }
    EXPECT_TRUE(ParseLine(line, &rid, &lid, &cost));
    EXPECT_GE(cost, 0);
    EXPECT_EQ(cost, test_connector_->GetTransitionCost(rid, lid));
  }
}

TEST_F(TestConnectorTest, DoNotBreakDefaultConnector) {
  // Check cache corruption
  const size_t kTestSize = 10000;

  // Use test connector
  {
    InputFileStream ifs(test_file_.c_str());
    EXPECT_TRUE(ifs != NULL);
    string header_line;
    EXPECT_TRUE(getline(ifs, header_line));

    string line;
    uint16 rid, lid;
    int cost;
    for (size_t i = 0; i < kTestSize; ++i) {
      if (!getline(ifs, line)) {
        break;
      }
      EXPECT_TRUE(ParseLine(line, &rid, &lid, &cost));
      EXPECT_GE(cost, 0);
      EXPECT_EQ(cost, test_connector_->GetTransitionCost(rid, lid));
    }
  }

  // Use default connector
  {
    InputFileStream ifs(data_file_.c_str());
    EXPECT_TRUE(ifs != NULL);
    string header_line;
    EXPECT_TRUE(getline(ifs, header_line));

    string line;
    uint16 rid, lid;
    int cost;
    for (size_t i = 0; i < kTestSize; ++i) {
      if (!getline(ifs, line)) {
        break;
      }
      EXPECT_TRUE(ParseLine(line, &rid, &lid, &cost));
      EXPECT_GE(cost, 0);
      EXPECT_EQ(cost, connector_->GetTransitionCost(rid, lid));
    }
  }
}

}  // namespace mozc