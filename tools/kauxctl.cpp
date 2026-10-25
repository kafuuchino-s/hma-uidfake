// SPDX-License-Identifier: GPL-2.0
// CLI adapter for the unchanged dcc8c199 NetlinkClient and shared kaux.h.
#include "netlink.hpp"
#include "status.hpp"

#include <algorithm>
#include <charconv>
#include <cstdio>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>

// NetlinkClient reports reachability through this UI hook. This CLI prints it;
// it does not link the author's module.prop-writing status.cpp implementation.
namespace uidfake {
void report_status(std::string_view text) {
  std::fprintf(stderr, "kauxctl: %.*s\n", static_cast<int>(text.size()), text.data());
}
}

static bool decimal(const std::string &text, std::uint32_t &out) {
  if (text.empty()) return false;
  const auto result = std::from_chars(text.data(), text.data() + text.size(), out);
  return result.ec == std::errc{} && result.ptr == text.data() + text.size();
}

static bool read_pairs(const char *file, uidfake::Pairs &pairs) {
  std::ifstream in(file);
  if (!in) { std::perror(file); return false; }
  std::string line;
  unsigned line_number = 0;
  while (std::getline(in, line)) {
    ++line_number;
    if (line.find_first_not_of(" \t\r") == std::string::npos) continue;
    std::istringstream fields(line);
    std::string caller, target, extra;
    uidfake::Pair pair;
    if (!(fields >> caller >> target) || (fields >> extra) ||
        !decimal(caller, pair.caller) || !decimal(target, pair.target) ||
        pair.caller < uidfake::kFirstAppUid || pair.target < uidfake::kFirstAppUid ||
        pair.caller == pair.target || pairs.size() >= uidfake::NetlinkClient::kMaxPairs) {
      std::fprintf(stderr, "invalid pair at line %u (two distinct app UIDs required)\n", line_number);
      return false;
    }
    pairs.push_back(pair);
  }
  if (in.bad() || pairs.empty()) {
    std::fprintf(stderr, "pair file must be readable and nonempty; no policy was sent\n");
    return false;
  }
  std::sort(pairs.begin(), pairs.end());
  pairs.erase(std::unique(pairs.begin(), pairs.end()), pairs.end());
  return true;
}

static void json_string(const char *value, std::size_t size) {
  std::putchar('"');
  for (std::size_t i = 0; i < size && value[i]; ++i) {
    const unsigned char c = static_cast<unsigned char>(value[i]);
    if (c == '"' || c == '\\') { std::putchar('\\'); std::putchar(c); }
    else if (c < 32 || c > 126) std::printf("\\u%04x", static_cast<unsigned>(c));
    else std::putchar(c);
  }
  std::putchar('"');
}

static int status(uidfake::NetlinkClient &client) {
  const auto st = client.status();
  if (!st) return 1;
  std::printf("{\"magic\":%u,\"size\":%u,\"version\":%u,\"flags\":%u,"
              "\"native\":%u,\"native_expected\":%u,\"compat\":%u,\"compat_expected\":%u,"
              "\"apk_inodes\":%u,\"apk_offered\":%u,\"apk_failed\":%u,\"apk_failed_total\":%u,"
              "\"lsm_state\":%d,\"lsm_error\":%d,\"last_error\":%d,\"apk_updates\":%u,"
              "\"va_bits\":%u,\"page_shift\":%u,\"lsm_target\":",
              st->magic, st->size, st->version, st->flags,
              st->native, st->native_expected, st->compat, st->compat_expected,
              st->apk_inodes, st->apk_offered, st->apk_failed, st->apk_failed_total,
              st->lsm_state, st->lsm_error, st->last_error, st->apk_updates,
              st->va_bits, st->page_shift);
  json_string(st->lsm_target, sizeof(st->lsm_target));
  std::puts("}");
  return 0;
}

int main(int argc, char **argv) {
  try {
    uidfake::NetlinkClient client;
    if (argc == 2 && std::string_view(argv[1]) == "--status") return status(client);
    if (argc == 3 && std::string_view(argv[1]) == "--apply-pairs") {
      uidfake::Pairs pairs;
      if (!read_pairs(argv[2], pairs)) return 2;
      if (!client.push(pairs)) return 1;
      std::printf("{\"commit_ack\":true,\"applied_pairs\":%zu}\n", pairs.size());
      return status(client);
    }
    std::fprintf(stderr, "usage: kauxctl --status | --apply-pairs FILE\n"
                         "FILE replaces the whole in-memory policy; one caller_uid target_uid pair per line.\n");
    return 2;
  } catch (const std::exception &e) {
    std::fprintf(stderr, "kauxctl: %s\n", e.what());
    return 1;
  }
}
