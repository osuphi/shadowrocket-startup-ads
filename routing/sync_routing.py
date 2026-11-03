"""Build public routing resources. Only downloads fixed, public repository paths."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
BM7 = 'blackmatrix7/ios_rule_script'
HAGEZI = 'hagezi/dns-blocklists'
SOURCES = ['YouTube', 'Google', 'GitHub', 'OneDrive', 'Bing', 'AppleProxy', 'Apple',
           'Microsoft', 'SteamCN', 'Steam', 'BiliBili', 'iQIYI', 'Bahamut', 'China',
           'OpenAI', 'Douyu', 'HuYa', 'WeChat', 'DingTalk', 'AliPay', 'UnionPay',
           'ChinaMobile', 'ChinaTelecom', 'ChinaUnicom']
DOMAIN_TYPES = {'DOMAIN', 'DOMAIN-SUFFIX'}
DOMAIN = re.compile(r'(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\Z')


def inside(host, suffix):
    return host == suffix or host.endswith('.' + suffix)


def valid_domain(value):
    return bool(DOMAIN.fullmatch(value)) and all(label and len(label) <= 63 and not label.startswith('-') and not label.endswith('-') for label in value.split('.'))


def fetch(url, limit=8_000_000):
    if not (url.startswith('https://raw.githubusercontent.com/') or url.startswith('https://api.github.com/repos/')):
        raise ValueError('Only fixed public GitHub sources are allowed')
    error = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'shadowrocket-precision-builder/3'}), timeout=40) as response:
                if response.url.split('/')[2] not in ('raw.githubusercontent.com', 'api.github.com'):
                    raise ValueError('Unexpected redirect')
                data = response.read(limit + 1)
            if not data or len(data) > limit:
                raise ValueError('Empty or oversized resource')
            text = data.decode('utf-8-sig')
            if '<html' in text[:1000].lower() or '<!doctype html' in text[:1000].lower():
                raise ValueError('HTML instead of a rule resource')
            return text
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError('Public-source download failed: ' + url) from error


def download(cache):
    cache.mkdir(parents=True, exist_ok=True)
    commits = {}
    for repo, branch in [(BM7, 'master'), (HAGEZI, 'main')]:
        info = json.loads(fetch('https://api.github.com/repos/' + repo + '/commits/' + branch))
        sha = info['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Invalid source commit')
        commits[repo] = sha
    jobs = [(name + '.list', f'https://raw.githubusercontent.com/{BM7}/{commits[BM7]}/rule/Shadowrocket/{name}/{name}.list') for name in SOURCES]
    jobs += [(name + '_Domain.list', f'https://raw.githubusercontent.com/{BM7}/{commits[BM7]}/rule/Shadowrocket/{name}/{name}_Domain.list') for name in ('Apple', 'China')]
    jobs.append(('hagezi-light.txt', f'https://raw.githubusercontent.com/{HAGEZI}/{commits[HAGEZI]}/wildcard/light-onlydomains.txt'))
    def one(job):
        filename, url = job
        content = fetch(url)
        return filename, content, {'url': url, 'sha256': hashlib.sha256(content.encode()).hexdigest()}
    downloaded = list(ThreadPoolExecutor(max_workers=6).map(one, jobs))
    metadata = {'commits': commits, 'sources': {filename: record for filename, _, record in downloaded}}
    for filename, content, _ in downloaded:
        (cache / filename).write_text(content, encoding='utf-8')
    (cache / 'sources.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    return metadata


def parse_bm7(text, domain_set=False):
    result = []
    for row in text.splitlines():
        row = row.strip()
        if not row or row.startswith(('#', ';')):
            continue
        parts = ('DOMAIN-SUFFIX' if row.startswith('.') else 'DOMAIN', row.lstrip('.')) if domain_set else tuple(row.split(','))
        kind = parts[0]
        if kind in DOMAIN_TYPES:
            if len(parts) != 2 or not valid_domain(parts[1].lower()):
                raise ValueError('Invalid domain rule: ' + row)
            parts = (kind, parts[1].lower())
        elif kind in ('IP-CIDR', 'IP-CIDR6'):
            if len(parts) not in (2, 3) or len(parts) == 3 and parts[2] != 'no-resolve':
                raise ValueError('Invalid CIDR options')
            ipaddress.ip_network(parts[1], strict=False)
        elif kind not in ('USER-AGENT', 'DOMAIN-KEYWORD', 'IP-ASN', 'GEOIP'):
            raise ValueError('Unexpected upstream type: ' + kind)
        result.append(parts)
    if not result:
        raise ValueError('Empty upstream list')
    return result


def normalize(name, rows, policy):
    accepted, skipped = [], Counter()
    if name == 'OpenAI':
        rows = rows + [tuple(row.split(',')[:2]) for row in policy['ai_core_rules']]
    for atom in rows + [tuple(row) for row in policy.get('category_additions', {}).get(name, [])]:
        kind, value = atom[:2]
        if kind not in DOMAIN_TYPES and not (name == 'China' and kind in ('IP-CIDR', 'IP-CIDR6')):
            skipped['non-domain-service-rule'] += 1
            continue
        if name == 'OpenAI' and not (value in policy['ai_exact'] or any(inside(value, suffix) for suffix in policy['ai_suffixes'])):
            skipped['shared-or-unreviewed-ai-host'] += 1
            continue
        if kind in ('IP-CIDR', 'IP-CIDR6'):
            atom = (kind, value, 'no-resolve')
        accepted.append(tuple(atom))
    unique = sorted(set(accepted))
    suffixes = {row[1] for row in unique if row[0] == 'DOMAIN-SUFFIX'}
    result = []
    for row in unique:
        value = row[1]
        ancestors = ['.'.join(value.split('.')[i:]) for i in range(1, len(value.split('.')))]
        covered = any(parent in suffixes for parent in ancestors) or row[0] == 'DOMAIN' and value in suffixes
        if row[0] in DOMAIN_TYPES and covered:
            skipped['redundant-under-same-policy-suffix'] += 1
        else:
            result.append(row)
    if not result:
        raise ValueError('Normalization emptied a required service: ' + name)
    return result, dict(skipped)


def conservative_ads(text, policy):
    hosts = set()
    for row in text.splitlines():
        row = row.strip().lower()
        if not row or row.startswith(('#', '!')):
            continue
        if not valid_domain(row) or '.' not in row:
            raise ValueError('Advertising source is not a plain domain list')
        hosts.add(row)
    if len(hosts) < 1000:
        raise ValueError('Advertising source unexpectedly small')
    # A suffix is used only for these explicitly reviewed advertising families.
    suffixes = set(policy['ad_suffix_families']) & hosts
    if not suffixes:
        raise ValueError('Reviewed advertising families disappeared')
    exact, skipped = set(), Counter()
    for host in hosts:
        if any(inside(host, suffix) for suffix in policy['protected_suffixes']):
            skipped['functional-or-live-protection'] += 1
        elif any(inside(host, suffix) for suffix in suffixes):
            skipped['covered-by-reviewed-ad-family'] += 1
        elif any(inside(host, suffix) for suffix in policy['ad_exact_families']):
            if host.split('.')[0] not in policy['ad_protected_first_labels']:
                exact.add(host)
            else:
                skipped['functional-first-label'] += 1
        elif len(host.split('.')) >= 3 and host.split('.')[0] in policy['ad_exact_first_labels']:
            exact.add(host)
        else:
            skipped['not-an-explicit-reviewed-ad-shape'] += 1
    return sorted([('DOMAIN-SUFFIX', host) for host in suffixes] + [('DOMAIN', host) for host in exact]), {'input_domains': len(hosts), 'exact_hosts': len(exact), 'suffix_families': sorted(suffixes), 'skipped': dict(skipped)}


def parse_config(text):
    sections, current = {}, None
    for row in text.splitlines():
        row = row.strip()
        if not row or row.startswith(('#', ';')):
            continue
        if row.startswith('[') and row.endswith(']'):
            current = row[1:-1]
            if current in sections:
                raise ValueError('Duplicate section')
            sections[current] = []
        else:
            if current is None:
                raise ValueError('Active content outside section')
            sections[current].append(row)
    return sections


def make_config(policy, repo):
    root = 'https://raw.githubusercontent.com/' + repo + '/main/routing/'
    rules = list(policy['local_rules'])
    rules += policy['essential_rules'] + policy['shared_rules'] + policy['functional_rules']
    for name, group in policy['service_order_before_ads']:
        rules.append('RULE-SET,' + root + 'lists/' + name + '.list,' + group)
    rules += policy['carrier_rules']
    rules += ['# Conservative ad endpoints; mixed telemetry/config/message hosts are not blanket-blocked.',
              'RULE-SET,' + root + 'ads/ConservativeAds.list,🛑 拦截广告']
    rules += policy['service_overrides'] + policy['download_rules']
    for name, group in policy['service_order_after_ads']:
        rules.append('RULE-SET,' + root + 'lists/' + name + '.list,' + group)
    rules += policy['retained_rules']
    rules += ['RULE-SET,' + root + 'lists/China.list,🇨🇳 国内网站', 'GEOIP,CN,🇨🇳 国内网站', 'FINAL,🐟 漏网之鱼']
    general = list(policy['general']) + ['update-url = ' + root + 'Shadowrocket-Precision.conf']
    groups = list(policy['groups'])
    groups += [name + ' = select,DIRECT,🔰 选择节点,policy-select-name=DIRECT' for name in policy['new_direct_groups']]
    return '\n'.join(['# Shadowrocket Precision v3 - compatibility-first routing',
                        '# Public routing only: no nodes, subscription credentials, certificates or MITM scripts.',
                        '# Service rules: blackmatrix7, normalized to domains; China also retains domestic CIDRs.',
                        '# Ads: conservative exact-endpoint subset of HaGeZi Multi LIGHT, not the complete list.',
                        '# This remote configuration can overwrite manual file edits. App settings control refresh.',
                        '', '[General]', *general, '', '[Proxy Group]', *groups, '', '[Rule]', *rules,
                        '', '[MITM]', 'enable = false', ''])


def expand(config, lists):
    records = []
    for row in parse_config(config)['Rule']:
        parts = row.split(',')
        if parts[0] == 'RULE-SET':
            name = parts[1].rsplit('/', 1)[1].removesuffix('.list')
            records.extend((atom, parts[2], name) for atom in lists[name])
        elif parts[0] == 'FINAL':
            records.append((('FINAL',), parts[1], 'main'))
        else:
            records.append(((parts[0], parts[1], *parts[3:]), parts[2], 'main'))
    return records


def route(records, host, country=None, asn=None):
    host = host.lower().rstrip('.')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    for atom, policy, origin in records:
        kind, value = atom[0], atom[1] if len(atom) > 1 else ''
        hit = kind == 'FINAL'
        if kind == 'DOMAIN':
            hit = host == value
        elif kind == 'DOMAIN-SUFFIX':
            hit = inside(host, value)
        elif kind in ('IP-CIDR', 'IP-CIDR6') and address:
            network = ipaddress.ip_network(value)
            hit = address.version == network.version and address in network
        elif kind == 'GEOIP' and address:
            hit = country is not None and country.upper() == value.upper()
        if hit:
            return {'policy': policy, 'origin': origin, 'match': ','.join(atom)}
    raise ValueError('Missing fallback')


def validate(config, lists, policy, repo):
    sections = parse_config(config)
    assert set(sections) == {'General', 'Proxy Group', 'Rule', 'MITM'}
    assert sections['MITM'] == ['enable = false']
    assert not re.search(r'(?im)^\s*(ca-p12|ca-passphrase)\s*=', config)
    assert not any(row.startswith(('IP-ASN,', 'DOMAIN-KEYWORD,', 'USER-AGENT,')) for row in sections['Rule'])
    groups = {}
    for row in sections['Proxy Group']:
        name, body = row.split('=', 1)
        name = name.strip()
        assert name not in groups
        parts = body.strip().split(',')
        assert parts[0] == 'select'
        groups[name] = parts[1:]
        for part in parts[1:]:
            if part.startswith('policy-regex-filter='):
                re.compile(part.split('=', 1)[1])
    builtins = {'PROXY', 'DIRECT', 'REJECT'}
    def visit(name, stack=()):
        if name in builtins:
            return
        assert name in groups and name not in stack
        for member in groups[name]:
            if '=' not in member:
                visit(member, stack + (name,))
    for name, choices in groups.items():
        visit(name)
        selected = [v.split('=', 1)[1] for v in choices if v.startswith('policy-select-name=')]
        assert not selected or selected[0] in choices
    rules = sections['Rule']
    assert rules[-1] == 'FINAL,🐟 漏网之鱼'
    assert len(rules) == len(set(rules))
    urls = []
    for row in rules:
        parts = row.split(',')
        target = parts[1] if parts[0] == 'FINAL' else parts[2]
        assert target in groups or target in builtins
        if parts[0] == 'RULE-SET':
            assert len(parts) == 3 and parts[1].startswith('https://raw.githubusercontent.com/' + repo + '/main/routing/')
            urls.append(parts[1])
    assert len(urls) == len(set(urls))
    assert len(urls) == len(lists)
    records = expand(config, lists)
    matcher_keys = [atom[:2] for atom, _, _ in records if atom[0] != 'FINAL']
    assert len(matcher_keys) == len(set(matcher_keys)), 'Duplicate expanded exact matcher'
    cases = []
    for entry in policy['test_cases']:
        actual = route(records, entry['host'], **entry.get('context', {}))
        if actual['policy'] != entry['expected']:
            raise ValueError('Route mismatch: ' + entry['host'] + ': ' + str(actual))
        cases.append({**entry, 'actual': actual, 'pass': True})
    ad_records = [(atom, 'REJECT', 'ads') for atom in lists['ConservativeAds']] + [(('FINAL',), 'PASS', 'fallback')]
    for host in policy['protected_test_hosts']:
        assert route(ad_records, host)['policy'] == 'PASS', 'Protected host blocked: ' + host
    # Update simulation: newly listed functional hosts must still be excluded by the builder.
    sample = '\n'.join(policy['ad_suffix_families'] + ['filler' + str(i) + '.example.org' for i in range(1001)] + policy['protected_test_hosts'])
    future_ads, _ = conservative_ads(sample, policy)
    future_records = [(atom, 'REJECT', 'future-ads') for atom in future_ads] + [(('FINAL',), 'PASS', 'fallback')]
    for host in policy['protected_test_hosts']:
        assert route(future_records, host)['policy'] == 'PASS'
    return {'groups': len(groups), 'main_rules': len(rules), 'remote_resources': len(urls),
            'expanded_exact_duplicate_matchers': 0,
            'route_cases_passed': len(cases), 'functional_hosts_protected': len(policy['protected_test_hosts']),
            'synthetic_update_protection_cases_passed': len(policy['protected_test_hosts']), 'cases': cases}


def build(cache, output, repo):
    policy = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
    metadata = json.loads((cache / 'sources.json').read_text(encoding='utf-8'))
    for filename, record in metadata['sources'].items():
        digest = hashlib.sha256((cache / filename).read_text(encoding='utf-8').encode()).hexdigest()
        assert digest == record['sha256'], 'Input snapshot hash mismatch'
    lists, normalization = {}, {}
    for name in SOURCES:
        rows = parse_bm7((cache / (name + '.list')).read_text(encoding='utf-8'))
        if name in ('Apple', 'China'):
            rows += parse_bm7((cache / (name + '_Domain.list')).read_text(encoding='utf-8'), domain_set=True)
        lists[name], normalization[name] = normalize(name, rows, policy)
    lists['ConservativeAds'], ad_status = conservative_ads((cache / 'hagezi-light.txt').read_text(encoding='utf-8'), policy)
    # Remove lower-priority exact duplicates using the actual expanded configuration order.
    seen, duplicate_log = {}, []
    order = [name for name, _ in policy['service_order_before_ads']] + ['ConservativeAds'] + [name for name, _ in policy['service_order_after_ads']] + ['China']
    assert len(order) == len(set(order)) == len(lists)
    config = make_config(policy, repo)
    for row in parse_config(config)['Rule']:
        parts = row.split(',')
        if parts[0] == 'RULE-SET':
            name = parts[1].rsplit('/', 1)[1].removesuffix('.list')
            kept = []
            for atom in lists[name]:
                key = atom[:2]
                if key in seen:
                    duplicate_log.append({'matcher': ','.join(key), 'kept': seen[key], 'removed_from': name})
                else:
                    seen[key] = name
                    kept.append(atom)
            lists[name] = kept
            if not kept:
                raise ValueError('Required category emptied after precedence checks: ' + name)
        elif parts[0] != 'FINAL':
            key = tuple(parts[:2])
            if key in seen:
                duplicate_log.append({'matcher': ','.join(key), 'kept': seen[key], 'removed_from': 'main'})
                config = config.replace(row + '\n', '')
            else:
                seen[key] = 'main'
    validation = validate(config, lists, policy, repo)
    old_status = output / 'Status.json'
    if old_status.exists():
        old = json.loads(old_status.read_text(encoding='utf-8'))
        for name, count in old['counts'].items():
            if len(lists[name]) < max(1, int(count * .5)):
                raise ValueError('Rule count fell by more than half: ' + name)
    files = {'Shadowrocket-Precision.conf': config}
    for name, rows in lists.items():
        folder = 'ads' if name == 'ConservativeAds' else 'lists'
        source_name = 'HaGeZi Multi LIGHT; conservative derivative, GPL-3.0' if folder == 'ads' else 'blackmatrix7/ios_rule_script; domain normalization, GPL-2.0'
        files[folder + '/' + name + '.list'] = '\n'.join(['# Precision v3 / ' + name, '# Source: ' + source_name, '# Modified: filtered and normalized; see ../policy.json and ../sync_routing.py.', *[','.join(atom) for atom in rows], ''])
    hashes = {name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()}
    status = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'version': 3,
              'source_metadata': metadata, 'counts': {name: len(rows) for name, rows in lists.items()},
              'normalization': normalization, 'ad_filtering': ad_status,
              'removed_lower_priority_exact_duplicates': duplicate_log,
              'file_sha256': hashes, 'validation': validation,
              'native_import_tested': False, 'live_app_playback_tested': False,
              'limits': ['Rule matching and generated-update simulations only, not live DNS, GeoIP database or iPhone execution.',
                         'Conservative advertising subset intentionally leaves some ads and trackers.',
                         'External modules can override this configuration and may cause independent compatibility issues.',
                         'China Broadnet crashes with VPN connected are not claimed fixed by domain routing.']}
    # No output is touched until all parsing, count checks and regressions pass.
    files['Status.json'] = json.dumps(status, ensure_ascii=False, indent=2) + '\n'
    output.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        target = output / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_bytes(content.encode('utf-8'))
        temporary.replace(target)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', default='osuphi/shadowrocket-startup-ads')
    parser.add_argument('--snapshot-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, default=HERE)
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
        raise ValueError('Invalid public repository name')
    if args.download_only:
        if args.snapshot_dir is None:
            raise ValueError('Download cache directory required')
        download(args.snapshot_dir)
        print('Public routing source snapshots downloaded')
        return
    if args.snapshot_dir:
        status = build(args.snapshot_dir, args.output_dir, args.repository)
    else:
        with tempfile.TemporaryDirectory(prefix='routing-public-sources-') as directory:
            cache = Path(directory)
            download(cache)
            status = build(cache, args.output_dir, args.repository)
    print(json.dumps({'status': 'PASS', **{key: value for key, value in status['validation'].items() if key != 'cases'},
                      'advertising_rules': status['counts']['ConservativeAds']}))


if __name__ == '__main__':
    main()
