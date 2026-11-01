"""Functional regression checks for the public startup module updater. GPL-3.0."""
import json
from pathlib import Path
import re
import unittest
import sync_module as sync

POLICY = json.loads((Path(__file__).parent / "reviewed_rules.json").read_text(encoding="utf-8"))


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.seed = next(r for r in POLICY["reviewed_rules"] if r["app"] == "麦当劳")

    def source(self, *lines, section="Map Local", app="麦当劳"):
        return "#!name=fixture\n[" + section + "]\n# > " + app + "\n" + "\n".join(lines)

    def test_reviewed_rule_keeps_approved_output(self):
        rows, _ = sync.select_rules(self.source(self.seed["source_rule"]), POLICY)
        self.assertEqual(rows[0]["pattern"], self.seed["pattern"])

    def test_new_splash_path_on_known_host_is_updated(self):
        source = self.source(r'^https://api\.mcd\.cn/bff/portal/home/splash_v3 data-type=text data="{}" header="Content-Type:application/json"')
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["selection"], "bounded-upstream-update")
        self.assertTrue(re.search(rows[0]["pattern"], 'https://api.mcd.cn/bff/portal/home/splash_v3'))

    def test_new_host_is_not_silently_added_to_mitm(self):
        source = self.source(r'^https://accounts\.mcd\.cn/home/splash data-type=text data="{}" header="Content-Type:application/json"')
        rows, skipped = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])
        self.assertEqual(skipped["new-host-requires-review"], 1)

    def test_non_capturing_hostname_alternation_and_port(self):
        pattern = r'^https?://(?:api\.pinduoduo\.com|api\.yangkeduo\.com):\d+/splash'
        canonical, hosts, _ = sync.authority(pattern)
        self.assertEqual(canonical, pattern)
        self.assertEqual(hosts, ['api.pinduoduo.com', 'api.yangkeduo.com'])

    def test_retired_endpoint_does_not_freeze_other_safe_updates(self):
        source = self.source(r'^https://api\.mcd\.cn/bff/portal/home/splash_v3 data-type=text data="{}" header="Content-Type:application/json"')
        rows, _ = sync.select_rules(source, POLICY)
        checks = sync.validate_rules(rows, POLICY, require_baseline=False)
        self.assertTrue(checks["retired_positive_fixtures"])

    def test_bank_app_is_not_added(self):
        rows, _ = sync.select_rules(self.source(r'^https://bank.example/splash - reject', section="URL Rewrite", app="Bank"), POLICY)
        self.assertEqual(rows, [])

    def test_mixed_content_branch_is_not_added(self):
        source = self.source(r'^https://api\.mcd\.cn/(splash|account) data-type=text data="{}" header="Content-Type:application/json"')
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])

    def test_generic_startup_configuration_is_not_added(self):
        source = self.source(r'^https://api\.mcd\.cn/splash/config data-type=text data="{}" header="Content-Type:application/json"')
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])

    def test_remote_response_file_is_not_added(self):
        source = self.source(r'^https://api\.mcd\.cn/splash data-type=file data="https://example.com/code"')
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])

    def test_script_section_never_executes(self):
        rows, _ = sync.select_rules(self.source('evil = type=http-response,script-path=https://example.com/code', section="Script"), POLICY)
        self.assertEqual(rows, [])

    def test_duplicate_entries_are_deduplicated(self):
        rows, _ = sync.select_rules(self.source(self.seed["source_rule"], self.seed["source_rule"]), POLICY)
        self.assertEqual(len(rows), 1)

    def test_reviewed_map_is_not_replaced_by_duplicate_reject(self):
        duplicate = self.seed['pattern'] + ' - reject'
        source = self.source(self.seed['source_rule']) + '\n[URL Rewrite]\n# > 麦当劳\n' + duplicate
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['section'], 'Map Local')

    def test_old_dated_campaign_is_not_newly_added(self):
        source = self.source(r'^https://l0\.51fanli\.net/app/images/splash/2022/a.jpg data-type=text data=" "', app='返利网')
        rows, _ = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])

    def test_large_upstream_loss_stops_publication(self):
        with self.assertRaises(ValueError):
            sync.validate_rules([], POLICY)

    def test_module_points_only_to_owners_filtered_file(self):
        row = {k: self.seed[k] for k in ("app", "section", "pattern", "action", "hosts")}
        module = sync.render_module([row], "example/reviewed-ads", "main", "fixture")
        self.assertIn('#!raw-url=https://raw.githubusercontent.com/example/reviewed-ads/main/StartupAds.module', module)
        self.assertNotIn('[Script]', module)
        self.assertNotIn('enable = true', module)
        self.assertNotIn('hostname = %APPEND% *', module)


if __name__ == "__main__":
    unittest.main()
