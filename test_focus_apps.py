"""Independent splash endpoint and response-preservation regressions. GPL-3.0."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

import sync_module as sync

ROOT = Path(__file__).parent
POLICY = json.loads((ROOT / 'reviewed_rules.json').read_text(encoding='utf-8'))


def selected_fixture_rows():
    # Fixtures are source declarations, not captured personal traffic.
    grouped = {}
    for seed in POLICY['reviewed_rules']:
        source_id = seed.get('source_id', 'common')
        source_section = seed.get('source_section', seed['section'])
        grouped.setdefault(source_id, []).extend(['[' + source_section + ']', '# > ' + seed['app'], seed['source_rule']])
    result = []
    for source_id, lines in grouped.items():
        source = '#!name=test\n' + '\n'.join(lines)
        if source_id == 'common':
            rows, _ = sync.select_rules(source, POLICY)
        else:
            rows, _ = sync.select_rules(source, POLICY, source_id=source_id)
        result.extend(rows)
    return result


class FocusAppTests(unittest.TestCase):
    def test_requested_app_splash_endpoints_have_specific_coverage(self):
        rows = selected_fixture_rows()
        cases = [
            ('https://app.bilibili.com/x/v2/splash/list?build=1', 'Body Rewrite'),
            ('https://app.bilibili.com/x/v2/splash/event/list2?build=1', 'Body Rewrite'),
            ('https://rtbapi.douyucdn.cn/japi/sign/app/getinfo?client_sys=ios', 'Map Local'),
            ('https://bootpreload.uve.weibo.com/v3/ad/preload?source=ios', 'Map Local'),
            ('https://bootrealtime.uve.weibo.com/v2/ad/realtime?source=ios', 'Map Local'),
            ('https://api.zhihu.com/commercial_api/launch_v2?platform=ios', 'Body Rewrite'),
            ('https://api.zhihu.com/commercial_api/real_time_launch_v2', 'Body Rewrite'),
        ]
        for url, section in cases:
            with self.subTest(url=url):
                hit = next((r for r in rows if re.search(r['pattern'], url)), None)
                self.assertIsNotNone(hit, 'No splash handler for ' + url)
                self.assertEqual(hit['section'], section)

    def test_focus_rules_do_not_intercept_normal_app_functions(self):
        rows = [r for r in selected_fixture_rows() if r['app'] in ('哔哩哔哩','斗鱼直播','微博','知乎')]
        normal = [
            'https://app.bilibili.com/x/v2/feed/index?build=1',
            'https://app.bilibili.com/x/v2/account/mine?build=1',
            'https://app.bilibili.com/x/v2/splash/listen?build=1',
            'https://app.bilibili.com.evil.example/x/v2/splash/list',
            'https://api.live.bilibili.com/xlive/app-room/v1/index/getInfoByRoom',
            'https://capi.douyucdn.cn/lapi/live/getH5Play/1',
            'https://capi.douyucdn.cn/api/ios_app/check_update',
            'https://rtbapi.douyucdn.cn/japi/sign/app/getinformation',
            'https://msg.douyu.com/login',
            'https://api.weibo.cn/2/statuses/friends_timeline',
            'https://api.weibo.cn/2/messages',
            'https://bootpreload.uve.weibo.com/v3/ad/preload_config',
            'https://api.zhihu.com/me',
            'https://api.zhihu.com/topstory/recommend',
            'https://api.zhihu.com/commercial_api/answer/123/bottom-v2',
            'https://api.zhihu.com/commercial_api/launch_v2_extra',
        ]
        for url in normal:
            with self.subTest(url=url):
                self.assertFalse(any(re.search(r['pattern'], url) for r in rows), url)

    def test_target_updates_do_not_add_whole_domain_rejects_or_scripts(self):
        rows = selected_fixture_rows()
        module = sync.render_module(rows, 'osuphi/shadowrocket-startup-ads', 'main', 'fixture')
        self.assertNotIn('[Rule]', module)
        self.assertNotIn('[Script]', module)
        self.assertNotIn('script-path=', module)
        self.assertNotIn('ca-p12=', module)
        hosts_line = next(l for l in module.splitlines() if l.startswith('hostname ='))
        self.assertNotIn('*.', hosts_line)

    def test_unreviewed_native_body_expression_is_not_added(self):
        source = '#!name=test\n[Body Rewrite]\n# > 知乎\nhttp-response-jq ^https://api\\.zhihu\\.com/launch '\
                 "'.account = {}'\n"
        rows, skipped = sync.select_rules(source, POLICY)
        self.assertEqual(rows, [])
        self.assertEqual(skipped['body-rewrite-requires-review'], 1)

    def test_lost_required_splash_coverage_stops_publication(self):
        rows = [r for r in selected_fixture_rows() if r['app'] != '哔哩哔哩']
        with self.assertRaises(ValueError):
            sync.validate_rules(rows, POLICY)

    def jq(self, app, value):
        executable = shutil.which('jq')
        if not executable:
            if os.environ.get('REQUIRE_JQ') == '1':
                self.fail('jq is required for publication response-fixture checks')
            self.skipTest('jq unavailable locally; cloud publication requires it')
        rows = selected_fixture_rows()
        row = next(r for r in rows if r['app'] == app and r['section'] == 'Body Rewrite')
        expression = row['action'][1:-1]
        run = subprocess.run([executable, '-c', expression], input=json.dumps(value), text=True, capture_output=True, check=True)
        return json.loads(run.stdout)

    def test_bilibili_response_keeps_metadata_and_unrelated_fields(self):
        original = {'code':0,'message':'0','ttl':1,'data':{'show':[{'id':1}],'event_list':[{'id':2}], 'list':[{'id':3}], 'keep':{'mode':'normal'}}}
        expected = copy.deepcopy(original)
        for key in ('show','event_list','list'):
            expected['data'][key] = []
        self.assertEqual(self.jq('哔哩哔哩', original), expected)
        for value in ({'code':-400,'data':None}, {'code':0,'data':{'keep':1}}, {'code':0,'data':{'list':'unsupported shape'}}):
            self.assertEqual(self.jq('哔哩哔哩', value), value)

    def test_zhihu_response_keeps_schema_and_embedded_json_types(self):
        embedded = {'img_play_duration':8,'launch_timeout':5,'keep':7}
        value = {'code':0,'data':{'img_play_duration':10,'launch_timeout':20,'keep':'normal', 'encoded':json.dumps(embedded)},'other':[1,2]}
        actual = self.jq('知乎', value)
        expected = copy.deepcopy(value)
        expected['data']['img_play_duration'] = 0
        expected['data']['launch_timeout'] = 0
        expected['data']['encoded'] = actual['data']['encoded']
        self.assertEqual(actual, expected)
        self.assertIsInstance(actual['data']['encoded'], str)
        self.assertEqual(json.loads(actual['data']['encoded']), {'img_play_duration':0,'launch_timeout':0,'keep':7})
        for item in ({'code':-1,'data':None}, {'code':0,'keep':'not JSON img_play_duration'}, {'code':0,'data':{'unknown':1}}, {'data':{'img_play_duration':'8','launch_timeout':None}}):
            self.assertEqual(self.jq('知乎', item), item)


if __name__ == '__main__':
    unittest.main()
