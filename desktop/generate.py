"""Render the desktop extension from the checked Shadowrocket routing output."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from routing.sync_routing import parse_config


HERE = Path(__file__).resolve().parent
PREFIX = '精细分流 · '
PROVIDER_PREFIX = 'fine-bm7-'
PRIMARY = '🔰 选择节点'
ADS = '🛑 拦截广告'
FALLBACK = '🐟 漏网之鱼'
REGION_PATTERNS = {
    '香港节点': r'香港|Hong[ -]?Kong|(?:^|[^A-Za-z])HK(?:[^A-Za-z]|$)|🇭🇰',
    '日本节点': r'日本|东京|大阪|Japan|Tokyo|(?:^|[^A-Za-z])JP(?:[^A-Za-z]|$)|🇯🇵',
    '新加坡节点': r'新加坡|狮城|Singapore|(?:^|[^A-Za-z])SG(?:[^A-Za-z]|$)|🇸🇬',
    '美国节点': r'美国|洛杉矶|圣何塞|西雅图|United[ -]?States|USA|(?:^|[^A-Za-z])US(?:[^A-Za-z]|$)|🇺🇸|🇺🇲',
    '台湾节点': r'台湾|台灣|台北|Taiwan|Taipei|(?:^|[^A-Za-z])TW(?:[^A-Za-z]|$)|🇹🇼',
}


def build_spec(source):
    groups = {'Bark': PREFIX + 'Bark'}
    direct_groups, proxy_groups = [], []
    for row in source['Proxy Group']:
        name, options = (part.strip() for part in row.split('=', 1))
        if 'policy-regex-filter=' in options:
            continue
        title = '节点选择' if name == PRIMARY else re.sub(r'^\W+', '', name)
        groups[name] = PREFIX + title
        if name in (PRIMARY, ADS, FALLBACK):
            continue
        default, = (part.split('=', 1)[1] for part in options.split(',')
                    if part.startswith('policy-select-name='))
        if default == 'DIRECT':
            direct_groups.append(name)
        elif default == PRIMARY:
            proxy_groups.append(name)
        else:
            raise ValueError(f'Unsupported desktop group default for {name}: {default}')
    if len(set(groups.values())) != len(groups):
        raise ValueError('Duplicate desktop group name')

    providers = {}
    rules = [f'DOMAIN,api.day.app,{groups["Bark"]}']
    for row in source['Rule']:
        kind, value, *tail = row.split(',')
        if kind == 'FINAL':
            rules.append(f'MATCH,{groups[value]}')
            continue
        policy, *options = tail
        if kind == 'RULE-SET':
            filename = Path(urlsplit(value).path).name
            name = PROVIDER_PREFIX + filename.removesuffix('.list')
            if name in providers or not filename.endswith('.list'):
                raise ValueError(f'Invalid or duplicate rule provider: {filename}')
            providers[name] = {
                'type': 'http', 'behavior': 'classical', 'format': 'text',
                'url': value, 'path': './ruleset/fine-precision/' + filename,
                'interval': 86400, 'proxy': groups[PRIMARY],
            }
            value = name
        rules.append(','.join((kind, value, groups.get(policy, policy), *options)))
    return {
        'version': 4, 'prefix': PREFIX, 'providerPrefix': PROVIDER_PREFIX, 'groups': groups,
        'directGroups': direct_groups, 'proxyGroups': proxy_groups,
        'regions': [{'name': PREFIX + name, 'pattern': regex} for name, regex in REGION_PATTERNS.items()],
        'providers': providers, 'rules': rules,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HERE.parent / 'routing/Shadowrocket-Precision.conf')
    parser.add_argument('--output', type=Path, default=HERE / 'Desktop-Routing.js')
    args = parser.parse_args()
    source = parse_config(args.config.read_text(encoding='utf-8'))
    data = build_spec(source)
    template = (HERE / 'routing-template.js').read_text(encoding='utf-8')
    marker = '/*__PUBLIC_DATA__*/'
    if template.count(marker) != 1:
        raise ValueError('Expected one desktop rule data placeholder')
    args.output.write_bytes(template.replace(marker, json.dumps(data, ensure_ascii=False, indent=2)).encode())
    print(f'Generated {len(data["rules"])} desktop rules and {len(data["providers"])} remote rule sets')


if __name__ == '__main__':
    main()
