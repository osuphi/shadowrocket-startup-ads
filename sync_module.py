#!/usr/bin/env python3
"""Regenerate a bounded startup-ad module from public rule data. GPL-3.0.

Original rules: fmz200/wool_scripts and contributors.
Modified 2026-11-02: reviewed endpoint selection, bounded hostname scope,
no remote scripts, generation checks, and user-owned module update URL.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
from re import _parser as parser, _constants as sc
import sys
import time
import urllib.request
from urllib.parse import urlsplit

SOURCE_URL = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Shadowrocket/module/blockAds.srmodule"
ROOT = Path(__file__).resolve().parent
SECTIONS = {"URL Rewrite", "Map Local"}
ACTIONS = {
    "URL Rewrite": {"- reject"},
    "Map Local": {'data-type=text data="{}" header="Content-Type:application/json"', 'data-type=text data=" "', 'data-type=tiny-gif'},
}
AD_PATH = re.compile(r"splash|start_?screen_?ads?|start_?page|launch_?ads?|open_?ads?|open_?screen|flash_?screen", re.I)
NON_AD_PATH = re.compile(r"login|account|receipt|pay(?:ment)?|token|userinfo|profile|init|config|dns|upgrade", re.I)


def finite(tokens, limit=32):
    values = [""]
    for op, arg in tokens:
        if op == sc.LITERAL:
            options = [chr(arg)]
        elif op == sc.SUBPATTERN:
            options = finite(arg[-1], limit)
        elif op == sc.BRANCH:
            options = [s for branch in arg[1] for s in finite(branch, limit)]
        elif op == sc.IN:
            options = []
            for kind, v in arg:
                if kind == sc.LITERAL:
                    options.append(chr(v))
                elif kind == sc.RANGE and v[1] - v[0] <= 10:
                    options.extend(chr(i) for i in range(v[0], v[1] + 1))
                elif kind == sc.CATEGORY and v == sc.CATEGORY_DIGIT:
                    options.extend("0123456789")
                else:
                    raise ValueError("non-finite hostname")
        elif op == sc.CATEGORY and arg == sc.CATEGORY_DIGIT:
            options = list("0123456789")
        elif op in (sc.MAX_REPEAT, sc.MIN_REPEAT) and arg[1] <= 2:
            unit = finite(arg[2], limit)
            options = []
            for count in range(arg[0], arg[1] + 1):
                options.extend("".join(p) for p in itertools.product(unit, repeat=count))
        else:
            raise ValueError("wildcard or unbounded hostname")
        values = [a + b for a in values for b in options]
        if len(values) > limit:
            raise ValueError("too many hostname expansions")
    return values


def authority(pattern):
    normalized = pattern.replace(r"\/", "/")
    m = re.fullmatch(r"(\^https?\??://)([^/]+)(/.*)", normalized)
    if not m:
        raise ValueError("unsupported authority")
    scheme, hostport, path = m.groups()
    depth, escaped, bracket, port_at = 0, False, False, None
    for index, char in enumerate(hostport):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "[":
            bracket = True
        elif char == "]":
            bracket = False
        elif not bracket and char == "(":
            depth += 1
        elif not bracket and char == ")":
            depth -= 1
        elif not bracket and char == ":" and depth == 0:
            port_at = index
            break
    hostname_pattern = hostport if port_at is None else hostport[:port_at]
    port = "" if port_at is None else hostport[port_at:]
    if port and not (port[1:].isdigit() or port[1:] == r"\d+"):
        raise ValueError("unsupported port pattern")
    hosts = sorted(set(finite(parser.parse(hostname_pattern, 0))))
    if not hosts or any(not re.fullmatch(r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+", h) or re.fullmatch(r"[0-9.]+", h) for h in hosts):
        raise ValueError("invalid hostname")
    host_pattern = "(?:" + "|".join(re.escape(h) for h in hosts) + ")" if len(hosts) > 1 else re.escape(hosts[0])
    canonical = scheme + host_pattern + port + path
    re.compile(canonical)
    return canonical, hosts, path


def parse_source(source):
    section, app = "", ""
    rows = []
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif line.startswith("# > "):
            app = line[4:].strip()
        elif section in SECTIONS and line and not line.startswith("#"):
            rows.append({"app": app, "section": section, "source_rule": line})
    return rows


def select_rules(source, policy):
    seeds = {(r["section"], r["source_rule"]): r for r in policy["reviewed_rules"]}
    allowed = defaultdict(set)
    for row in policy["reviewed_rules"]:
        allowed[row["app"]].update(row["hosts"])
    upstream_rows = parse_source(source)
    active_reviewed_patterns = {seeds[(r["section"], r["source_rule"])]["pattern"] for r in upstream_rows if (r["section"], r["source_rule"]) in seeds}
    chosen, seen = [], set()
    skipped = Counter()
    for upstream in upstream_rows:
        key = (upstream["section"], upstream["source_rule"])
        if key in seeds:
            seed = seeds[key]
            row = {k: seed[k] for k in ("app", "section", "pattern", "action", "hosts")}
            row["selection"] = "reviewed-endpoint"
        else:
            if upstream["app"] not in allowed:
                skipped["app-not-reviewed"] += 1
                continue
            try:
                pattern, action = upstream["source_rule"].split(" ", 1)
                if action not in ACTIONS[upstream["section"]]:
                    skipped["action-not-allowed"] += 1
                    continue
                canonical, hosts, path = authority(pattern)
                if canonical in active_reviewed_patterns:
                    skipped["already-covered-by-reviewed-rule"] += 1
                    continue
                if not set(hosts) <= allowed[upstream["app"]]:
                    skipped["new-host-requires-review"] += 1
                    continue
                # New rules must be simple startup-ad paths, not mixed branches or
                # generic app initialization. Reviewed narrowed exceptions remain above.
                path_only = path.split(r"\?", 1)[0]
                dated = re.search(r"/(20\d{2})/", path_only)
                if dated and int(dated.group(1)) < datetime.now(timezone.utc).year:
                    skipped["dated-historical-rule"] += 1
                    continue
                if len(canonical) > 600 or "|" in path or "(?" in path or re.search(r"\\[1-9]", path):
                    skipped["complex-or-mixed-new-path"] += 1
                    continue
                if not AD_PATH.search(path_only) or NON_AD_PATH.search(path):
                    skipped["not-explicit-startup-ad"] += 1
                    continue
                row = {"app": upstream["app"], "section": upstream["section"], "pattern": canonical,
                       "action": action, "hosts": hosts, "selection": "bounded-upstream-update"}
            except (ValueError, re.error):
                skipped["unsupported-new-rule"] += 1
                continue
        dedupe = (row["section"], row["pattern"])
        if dedupe not in seen:
            seen.add(dedupe)
            chosen.append(row)
    return chosen, dict(skipped)


def validate_rules(rows, policy, require_baseline=True):
    if require_baseline and len(rows) < policy["minimum_rule_count"]:
        raise ValueError("Upstream format/coverage changed too much; retain the last published module")
    allowed_hosts = {h for row in policy["reviewed_rules"] for h in row["hosts"]}
    compiled = []
    for row in rows:
        if row["section"] not in SECTIONS or row["action"] not in ACTIONS[row["section"]]:
            raise ValueError("unapproved rule type/action")
        canonical, hosts, _ = authority(row["pattern"])
        if canonical != row["pattern"] or not set(hosts) <= allowed_hosts:
            raise ValueError("hostname scope expanded outside review")
        regex = re.compile(row["pattern"])
        for host in hosts:
            for normal in ("/login", "/api/user/profile", "/pay/create", "/api/order/list", "/api/getNewsRemoteConfig"):
                if regex.search("https://" + host + normal):
                    raise ValueError("rule captures a normal endpoint")
        compiled.append((row, regex))
    retired = []
    for case in policy["regression_cases"]:
        hit = next((row for row, regex in compiled if regex.search(case["url"])), None)
        actual = hit["section"] if hit else None
        if case["expected_section"] is None and actual is not None:
            raise ValueError("Normal/protected request would be intercepted; retain last publication: " + case["url"])
        if case["expected_section"] is not None and actual is None:
            # A retired upstream endpoint must not freeze all future updates. Track it
            # in public status while still enforcing minimum coverage and all negatives.
            retired.append(case["url"])
    return {"retired_positive_fixtures": retired, "protected_request_fixtures": sum(c["expected_section"] is None for c in policy["regression_cases"])}


def render_module(rows, repository, branch, upstream_date):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", branch):
        raise ValueError("invalid branch")
    url = f"https://raw.githubusercontent.com/{repository}/{branch}/StartupAds.module"
    lines = [
        "#!name=开屏广告增强（自动同步筛选版）",
        "#!desc=公开上游规则自动同步；限已审阅应用和主机。需 HTTPS 解密及自己的受信任 CA，不保证所有 App/版本生效。",
        "#!author=Modified from fmz200/wool_scripts and contributors",
        "#!homepage=https://github.com/" + repository,
        "#!raw-url=" + url,
        "# GPL-3.0. Modified 2026-11-02. See LICENSE and README.md.",
        "# Upstream source: " + SOURCE_URL,
        "# Upstream date: " + upstream_date,
        "# This generated subset does not include remote-execution scripts or certificate material.",
    ]
    for section in ("URL Rewrite", "Map Local"):
        lines.extend(["", "[" + section + "]"])
        for row in rows:
            if row["section"] == section:
                lines.extend(["# " + row["app"], row["pattern"] + " " + row["action"]])
    hosts = sorted({h for row in rows for h in row["hosts"]})
    lines.extend(["", "[MITM]", "hostname = %APPEND% " + ", ".join(hosts), ""])
    return "\n".join(lines)


def download():
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "startup-module-reviewed-sync/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                final = urlsplit(response.geturl())
                if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
                    raise ValueError("unexpected download destination")
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError("upstream too large")
            text = data.decode("utf-8-sig")
            if "[URL Rewrite]" not in text or "[Map Local]" not in text or not text.startswith("#!"):
                raise ValueError("not the expected module format")
            return text
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError("Public upstream download failed; existing module is unchanged") from last_error


def write_atomic(path, value):
    temporary = path.with_name(path.name + ".new")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--branch", default="main")
    ap.add_argument("--source-file", type=Path, help="Offline public fixture; normal scheduled runs download the fixed upstream URL")
    ap.add_argument("--output-dir", type=Path, default=ROOT)
    args = ap.parse_args()
    policy = json.loads((ROOT / "reviewed_rules.json").read_text(encoding="utf-8"))
    source = args.source_file.read_text(encoding="utf-8") if args.source_file else download()
    rows, skipped = select_rules(source, policy)
    checked = validate_rules(rows, policy)
    updated = re.search(r"^#!date=(.*)$", source, re.M)
    upstream_date = updated.group(1).strip() if updated else "not supplied"
    content = render_module(rows, args.repository, args.branch, upstream_date)
    current = args.output_dir / "StartupAds.module"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    changed = not current.exists() or current.read_text(encoding="utf-8") != content
    if changed:
        write_atomic(current, content)
    status = {
        "checked_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "upstream": SOURCE_URL, "upstream_date": upstream_date,
        "upstream_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "module_sha256": hashlib.sha256(current.read_bytes()).hexdigest(),
        "module_changed": changed, "rules": len(rows),
        "input_mode": "local-public-fixture" if args.source_file else "public-download",
        "app_labels": len({r["app"] for r in rows}),
        "exact_hosts": len({h for r in rows for h in r["hosts"]}),
        "bounded_updates": sum(r["selection"] == "bounded-upstream-update" for r in rows),
        "skipped": skipped, "regression_cases": len(policy["regression_cases"]),
        **checked,
    }
    write_atomic(args.output_dir / "UpdateStatus.json", json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
