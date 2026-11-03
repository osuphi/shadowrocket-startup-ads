import json
from pathlib import Path
import tempfile
import unittest

import sync_routing as sync

POLICY = json.loads((Path(__file__).parent / 'policy.json').read_text(encoding='utf-8'))


class RoutingBoundaryTests(unittest.TestCase):
    def source(self, *hosts):
        return '\n'.join(['filler' + str(i) + '.example.org' for i in range(1001)] + ['googlesyndication.com', 'adnxs.com'] + list(hosts))

    def ads_route(self, content, host):
        rows, _ = sync.conservative_ads(content, POLICY)
        records = [(row, 'REJECT', 'ads') for row in rows] + [(('FINAL',), 'PASS', 'fallback')]
        return sync.route(records, host)['policy']

    def test_functional_hosts_not_reintroduced_by_upstream_update(self):
        content = self.source(*POLICY['protected_test_hosts'])
        for host in POLICY['protected_test_hosts']:
            with self.subTest(host=host):
                self.assertEqual(self.ads_route(content, host), 'PASS')

    def test_ad_hostname_is_exact_not_implicitly_suffix(self):
        content = self.source('ads.publisher.example')
        self.assertEqual(self.ads_route(content, 'ads.publisher.example'), 'REJECT')
        self.assertEqual(self.ads_route(content, 'child.ads.publisher.example'), 'PASS')

    def test_no_parent_promotion_from_ad_endpoint(self):
        content = self.source('ad.ae.doubleclick.net')
        self.assertEqual(self.ads_route(content, 'ad.ae.doubleclick.net'), 'REJECT')
        self.assertEqual(self.ads_route(content, 'doubleclick.net'), 'PASS')
        self.assertEqual(self.ads_route(content, 'accounts.doubleclick.net'), 'PASS')

    def test_reviewed_suffix_boundary(self):
        content = self.source()
        self.assertEqual(self.ads_route(content, 'pagead2.googlesyndication.com'), 'REJECT')
        self.assertEqual(self.ads_route(content, 'googlesyndication.com.example.net'), 'PASS')
        self.assertEqual(self.ads_route(content, 'notgooglesyndication.com'), 'PASS')

    def test_new_ad_family_root_does_not_expand_to_its_children(self):
        content = self.source('doubleclick.net', 'accounts.doubleclick.net')
        self.assertEqual(self.ads_route(content, 'doubleclick.net'), 'REJECT')
        self.assertEqual(self.ads_route(content, 'accounts.doubleclick.net'), 'PASS')
        self.assertEqual(self.ads_route(content, 'unlisted.doubleclick.net'), 'PASS')

    def test_message_api_and_telemetry_names_are_not_ads(self):
        hosts = ['msg.publisher.example', 'api.publisher.example', 'config.publisher.example',
                 'push.publisher.example', 'telemetry.publisher.example', 'stats.publisher.example',
                 'adsense.publisher.example', 'adventure.publisher.example']
        for host in hosts:
            self.assertEqual(self.ads_route(self.source(*hosts), host), 'PASS')

    def test_sensitive_first_label_within_ad_family(self):
        for host in ('accounts.doubleclick.net', 'config.doubleclick.net', 'auth.adsrvr.org'):
            self.assertEqual(self.ads_route(self.source(host), host), 'PASS')

    def test_malformed_ads_not_silently_accepted(self):
        for bad in ('<html>error</html>', '||ads.example.com^', '*.example.com', 'example.com,REJECT', 'bad..example.com'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sync.conservative_ads(self.source(bad), POLICY)

    def test_truncated_ad_source_rejected(self):
        with self.assertRaises(ValueError):
            sync.conservative_ads('ads.example.net\n', POLICY)

    def test_service_does_not_capture_shared_ip_asn_or_keyword(self):
        rows = sync.parse_bm7('DOMAIN-SUFFIX,google.com\nIP-CIDR,1.2.3.0/24,no-resolve\nIP-ASN,12345,no-resolve\nDOMAIN-KEYWORD,google\nUSER-AGENT,Google*\n')
        result, _ = sync.normalize('Google', rows, POLICY)
        self.assertEqual(result, [('DOMAIN-SUFFIX', 'google.com')])

    def test_china_keeps_valid_cidrs_without_new_resolution(self):
        rows = sync.parse_bm7('DOMAIN-SUFFIX,example.cn\nIP-CIDR,1.2.3.0/24\n')
        result, _ = sync.normalize('China', rows, POLICY)
        self.assertIn(('IP-CIDR', '1.2.3.0/24', 'no-resolve'), result)

    def test_openai_does_not_take_over_shared_providers(self):
        rows = sync.parse_bm7('DOMAIN-SUFFIX,openai.com\nDOMAIN-SUFFIX,sentry.io\nDOMAIN-SUFFIX,auth0.com\nIP-ASN,20473,no-resolve\n')
        result, _ = sync.normalize('OpenAI', rows, POLICY)
        self.assertIn(('DOMAIN-SUFFIX', 'openai.com'), result)
        self.assertFalse(any(row[0] not in sync.DOMAIN_TYPES or row[1] in ('sentry.io','auth0.com') for row in result))

    def test_domain_pair_and_same_policy_redundancy(self):
        rows = sync.parse_bm7('.apple.com\n', domain_set=True) + sync.parse_bm7('DOMAIN,api.apple.com\nDOMAIN-SUFFIX,apple.com\n')
        result, _ = sync.normalize('Apple', rows, POLICY)
        self.assertEqual(result, [('DOMAIN-SUFFIX', 'apple.com')])

    def test_onedrive_shortener_replaces_broad_keyword(self):
        result, _ = sync.normalize('OneDrive', [('DOMAIN-KEYWORD', '1drv')], POLICY)
        records = [(row, 'OneDrive', 'source') for row in result] + [(('FINAL',), 'PASS', 'fallback')]
        self.assertEqual(sync.route(records, '1drv.ms')['policy'], 'OneDrive')
        self.assertEqual(sync.route(records, 'not1drv.ms')['policy'], 'PASS')

    def test_unknown_upstream_syntax_rejected(self):
        for value in ('SCRIPT,run\n', 'DOMAIN,*.example.com\n', 'DOMAIN,example.com,REJECT\n', 'IP-CIDR,not-a-cidr\n'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sync.parse_bm7(value)

    def test_source_failure_leaves_existing_outputs_unchanged(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(Path(__file__).resolve().parent))
            cache, output = root / 'cache', root / 'output'
            cache.mkdir()
            output.mkdir()
            (cache / 'sources.json').write_text('{"sources":{}}', encoding='utf-8')
            (cache / 'YouTube.list').write_text('<html>not a ruleset</html>', encoding='utf-8')
            sentinel = output / 'Shadowrocket-Precision.conf'
            sentinel.write_bytes(b'previous checked config')
            with self.assertRaises(ValueError):
                sync.build(cache, output, 'osuphi/shadowrocket-startup-ads')
            self.assertEqual(sentinel.read_bytes(), b'previous checked config')
            self.assertEqual(len(list(output.iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
