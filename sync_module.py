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
EXTRA_SOURCE_URLS = {"weibo": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Shadowrocket/module/weibo.srmodule"}
REVISION = '2026-11-11.2'
ROOT = Path(__file__).resolve().parent
BODY_TRANSFORMS = {
    'taobao-splash': 'def clean: if type == "array" then map(clean) elif type == "object" then with_entries(if .key == "taobao-splash" and (.value | type) == "object" then .value |= (if (.data | type) == "array" then .data = [] else . end) else .value |= clean end) else . end; clean',
    'jd-start': 'if type == "object" then (if (.images | type) == "array" then .images = [] else . end) | (if (.showTimesDaily | type) == "number" then .showTimesDaily = 0 else . end) else . end',
    'xhs-splash': 'if type == "object" then if (.data | type) == "object" then (if (.data.ads_groups | type) == "array" then .data.ads_groups = [] else . end) | del(.data.splash, .data.loading_img) else . end else . end',
    'iqiyi-ad': 'if type == "object" then if .errorCode == 0 then del(.adSlots, .splashLottieFile, .splashUiConfig) else . end else . end',
    'youku-ad': 'if type == "object" then if (.data | type) == "object" then if (.data.data | type) == "object" then del(.data.data.ad, .data.data.ykad) else . end else . end else . end',
    'smzdm-loading': 'if type == "object" then del(.data) else . end',
    'rail-ad': 'if type == "object" then (if (.materialsList | type) == "array" then .materialsList = [] else . end) | (if (.advertParam | type) == "object" and (.advertParam.skipTime | type) == "number" then .advertParam.skipTime = 0 else . end) else . end',
    'luckin-ad': 'if type == "object" then {status:"SUCCESS"} else . end',
    "bilibili-splash": 'if type == "object" then if (.data | type) == "object" then .data |= with_entries(if (.key == "show" or .key == "event_list" or .key == "list") and (.value | type) == "array" then .value = [] else . end) else . end else . end',
    "zhihu-launch": 'def clean: if type == "array" then map(clean) elif type == "object" then with_entries(.value |= clean) | (if has("img_play_duration") and (.img_play_duration | type) == "number" then .img_play_duration = 0 else . end) | (if has("launch_timeout") and (.launch_timeout | type) == "number" then .launch_timeout = 0 else . end) elif type == "string" and (contains("img_play_duration") or contains("launch_timeout")) then . as $original | try (fromjson | clean | tojson) catch $original else . end; clean',
}
SECTIONS = {"URL Rewrite", "Map Local", "Body Rewrite", "Rule"}
ACTIONS = {
    "URL Rewrite": {"- reject"},
    "Map Local": {'data-type=text data="{}" header="Content-Type:application/json"', 'data-type=text data="{}" status-code=200 header="Content-Type:application/json"', 'data-type=text data=" "', 'data-type=tiny-gif'},
    "Body Rewrite": {"'" + expression + "'" for expression in BODY_TRANSFORMS.values()},
    'Rule': {'REJECT'},
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
            app = ""
        elif line.startswith("# > "):
            app = line[4:].strip()
        elif section in (SECTIONS | {'Script'}) and line and not line.startswith("#"):
            rows.append({"app": app, "section": section, "source_rule": line})
    return rows


def select_rules(source, policy, source_id="common"):
    seeds = {(r.get("source_section", r["section"]), r["source_rule"]): r for r in policy["reviewed_rules"] if r.get("source_id", "common") == source_id}
    allowed = defaultdict(set)
    for row in policy["reviewed_rules"]:
        allowed[row["app"]].update(row["hosts"])
    for app, hosts in policy.get('auto_update_hosts', {}).items():
        allowed[app].update(hosts)
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
            if upstream['section'] in ('Rule', 'Script'):
                skipped['native-rule-or-script-source-requires-review'] += 1
                continue
            if upstream['section'] == 'Body Rewrite':
                skipped['body-rewrite-requires-review'] += 1
                continue
            if any(seed['app'] == upstream['app'] and seed['section'] == 'Body Rewrite' for seed in policy['reviewed_rules']):
                skipped['response-preservation-requires-review'] += 1
                continue
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
                if re.search(r'(?<!\\)[A-Za-z0-9_]$', canonical):
                    canonical += r'(?:/|\?|$)'
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
    allowed_hosts.update(h for hosts in policy.get('auto_update_hosts', {}).values() for h in hosts)
    compiled = []
    for row in rows:
        if row["section"] not in SECTIONS or row["action"] not in ACTIONS[row["section"]]:
            raise ValueError("unapproved rule type/action")
        if row['section'] == 'Rule':
            if row['pattern'] not in policy.get('dedicated_splash_domain_allowlist', []) or row['hosts']:
                raise ValueError('Unreviewed native domain block')
            regex = re.compile(r'^https?://' + re.escape(row['pattern']) + r'(?::\d+)?/')
            compiled.append((row, regex))
            continue
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
        if case['expected_section'] is not None and actual is not None and actual != case['expected_section']:
            raise ValueError('Unexpected response handling for reviewed endpoint: ' + case['url'])
        if case["expected_section"] is not None and actual is None:
            if require_baseline and case['url'] in policy.get('required_focus_urls', []):
                raise ValueError('Required app splash coverage disappeared; retain previous publication: ' + case['url'])
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
        "#!desc=修订 " + REVISION + "；按类别补全开屏及明确广告接口。需自己的受信任 CA，覆盖与限制见仓库 Coverage.md。",
        "#!author=Modified from fmz200/wool_scripts and contributors",
        "#!homepage=https://github.com/" + repository,
        "#!raw-url=" + url,
        '#!date=' + REVISION[:10],
        "# Revision: " + REVISION + " / category-wide reviewed startup coverage.",
        "# GPL-3.0. Modified 2026-11-11. See LICENSE and README.md.",
        "# Upstream source: " + SOURCE_URL,
        "# Supplemental source: " + EXTRA_SOURCE_URLS['weibo'],
        "# Upstream date: " + upstream_date,
        "# This generated subset does not include remote-execution scripts or certificate material.",
    ]
    for section in ('Rule', "URL Rewrite", "Body Rewrite", "Map Local"):
        lines.extend(["", "[" + section + "]"])
        for row in rows:
            if row["section"] == section:
                if section == 'Rule':
                    lines.extend(['# ' + row['app'], 'DOMAIN,' + row['pattern'] + ',REJECT'])
                    continue
                prefix = 'http-response-jq ' if section == 'Body Rewrite' else ''
                lines.extend(["# " + row["app"], prefix + row["pattern"] + " " + row["action"]])
    hosts = sorted({h for row in rows for h in row["hosts"]})
    lines.extend(["", "[MITM]", "hostname = %APPEND% " + ", ".join(hosts), ""])
    return "\n".join(lines)


def download(source_url=SOURCE_URL):
    if source_url not in {SOURCE_URL, *EXTRA_SOURCE_URLS.values()}:
        raise ValueError('Unapproved public source URL')
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(source_url, headers={"User-Agent": "startup-module-reviewed-sync/2.0"})
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


def coverage_report(rows, policy, source):
    catalog = json.loads((ROOT / 'coverage_catalog.json').read_text(encoding='utf-8'))
    counts = Counter(row['app'] for row in rows)
    entries = []
    for entry in catalog['apps']:
        count = sum(counts[app] for app in entry['source_apps'])
        state = ('部分广告接口' if entry.get('partial') else '已有针对性规则') if count else '待完善'
        entries.append({**entry, 'state':state, 'active_rule_count':count,
                        'device_tested':False})
    seeds = {(r.get('source_section',r['section']),r['source_rule']) for r in policy['reviewed_rules'] if r.get('source_id','common') == 'common'}
    pending = []
    for row in parse_source(source):
        if (row['section'],row['source_rule']) in seeds:
            continue
        if row['section'] in ('URL Rewrite','Map Local','Body Rewrite','Script') and re.search(r'splash|open.?screen|open.?ad|launch|startup|开屏',row['source_rule'],re.I):
            pending.append({'app':row['app'],'section':row['section'], 'declaration_preview':row['source_rule'][:400],
                            'status':'发现候选，不代表已启用或实测'})
    summary = {'catalog_apps':len(entries), 'categories':len(catalog['categories']),
               'with_configured_rules':sum(e['active_rule_count']>0 for e in entries),
               'pending_catalog_apps':sum(e['active_rule_count']==0 for e in entries),
               'all_selected_app_labels':len(counts), 'app_versions_device_tested':0,
               'new_or_unadopted_startup_candidates':len(pending)}
    report = {'revision':REVISION, 'summary':summary, 'apps':entries,
              'review_candidates':pending,
              'note':'规则与合成响应检查不等于设备实测。已配置、部分接口、待完善分别列示；不将应用标签数当作已验证 App 数量。'}
    md = ['# 主流应用覆盖清单', '', '修订：'+REVISION, '',
          f"已专项检查 {len(entries)} 个常用 App，分为 {summary['categories']} 类；其中 {summary['with_configured_rules']} 个有针对性或部分广告规则，{summary['pending_catalog_apps']} 个仍待完善。", '',
          '**本清单没有把任何应用标为实机验证成功。** 模块包含的其他应用标签另计；所有接口均来自公开源或明确审核的收窄版本。部分规则会拦截广告专用主机上的其他广告，不限开屏。', '',
          '| 分类 | App | 当前状态 | 生效规则数 | 范围与限制 |', '|---|---|---|---:|---|']
    for entry in entries:
        note = entry['scope_note'] or ('具体接口已配置；缓存、应用版本和 TLS 行为需设备验证。' if entry['active_rule_count'] else '没有已采用的可靠开屏接口，未用普通配置、消息或播放接口凑数。')
        md.append('| '+entry['category']+' | '+entry['app']+' | '+entry['state']+' | '+str(entry['active_rule_count'])+' | '+note.replace('|','/')+' |')
    md += ['', '## 自动维护范围', '',
           '每日重新获取上游并生成本表。已审核 App 的有限主机名单内，新增的简单开屏路径可在通过保护检查后自动纳入；未知主机、正文表达式、脚本和混合业务路径继续进入候选清单。Coverage.json 同时保存未采用的启动/开屏候选，不需要等用户点名才发现缺口。', '',
           '候选存在并不表示已经有可安全采用的实现。自动任务不承诺自行理解新的私有协议或适配所有 App 版本。', '']
    return report, '\n'.join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--branch", default="main")
    ap.add_argument("--source-file", type=Path, help="Offline public fixture; normal scheduled runs download the fixed upstream URL")
    ap.add_argument("--weibo-source-file", type=Path, help="Offline public Weibo fixture")
    ap.add_argument("--output-dir", type=Path, default=ROOT)
    args = ap.parse_args()
    policy = json.loads((ROOT / "reviewed_rules.json").read_text(encoding="utf-8"))
    source = args.source_file.read_text(encoding="utf-8") if args.source_file else download()
    rows, skipped = select_rules(source, policy)
    extra_source = args.weibo_source_file.read_text(encoding='utf-8') if args.weibo_source_file else download(EXTRA_SOURCE_URLS['weibo'])
    extra_rows, extra_skipped = select_rules(extra_source, policy, source_id='weibo')
    rows.extend(extra_rows)
    for reason, count in extra_skipped.items():
        skipped['weibo:' + reason] = count
    checked = validate_rules(rows, policy)
    updated = re.search(r"^#!date=(.*)$", source, re.M)
    upstream_date = updated.group(1).strip() if updated else "not supplied"
    content = render_module(rows, args.repository, args.branch, upstream_date)
    coverage, coverage_md = coverage_report(rows, policy, source)
    current = args.output_dir / "StartupAds.module"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    changed = not current.exists() or current.read_text(encoding="utf-8") != content
    if changed:
        write_atomic(current, content)
    write_atomic(args.output_dir / 'Coverage.json', json.dumps(coverage, ensure_ascii=False, indent=2)+'\n')
    write_atomic(args.output_dir / 'Coverage.md', coverage_md)
    status = {
        "checked_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "upstream": SOURCE_URL, "upstream_date": upstream_date,
        "upstream_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "module_sha256": hashlib.sha256(current.read_bytes()).hexdigest(),
        "module_changed": changed, "rules": len(rows),
        "revision": REVISION,
        'coverage_summary': coverage['summary'],
        "section_counts": dict(Counter(r['section'] for r in rows)),
        "focus_app_counts": {app:sum(r['app'] == app for r in rows) for app in ('哔哩哔哩','斗鱼直播','微博','知乎')},
        "supplemental_sources": {"weibo": {"url": EXTRA_SOURCE_URLS['weibo'], "sha256": hashlib.sha256(extra_source.encode()).hexdigest()}},
        "input_mode": "local-public-fixture" if args.source_file else "public-download",
        "app_labels": len({r["app"] for r in rows}),
        "exact_hosts": len({h for r in rows for h in r["hosts"]}),
        'native_exact_ad_domain_rules':sum(r['section']=='Rule' for r in rows),
        'pre_reviewed_update_hosts':len({h for hs in policy.get('auto_update_hosts',{}).values() for h in hs}),
        "bounded_updates": sum(r["selection"] == "bounded-upstream-update" for r in rows),
        "skipped": skipped, "regression_cases": len(policy["regression_cases"]),
        **checked,
    }
    write_atomic(args.output_dir / "UpdateStatus.json", json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
