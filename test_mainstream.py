"""Broad mainstream coverage, mixed-interface protection and real jq response checks."""
import json
import copy
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import urlsplit

import sync_module as sync
from test_focus_apps import selected_fixture_rows

ROOT = Path(__file__).parent
POLICY = json.loads((ROOT/'reviewed_rules.json').read_text(encoding='utf-8'))


class MainstreamTests(unittest.TestCase):
    def hit(self, rows, url):
        for row in rows:
            if row['section']=='Rule':
                if urlsplit(url).hostname == row['pattern']:
                    return row
            elif re.search(row['pattern'], url):
                return row
        return None

    def test_all_mainstream_positive_and_business_protection_fixtures(self):
        rows = selected_fixture_rows()
        for case in POLICY['regression_cases']:
            with self.subTest(url=case['url']):
                found = self.hit(rows,case['url'])
                self.assertEqual(found['section'] if found else None,case['expected_section'])

    def test_important_new_platforms_have_independent_startup_rules(self):
        rows=selected_fixture_rows()
        cases={
          '京东':'https://api.m.jd.com/client.action?functionId=start&client=apple',
          '小红书':'https://edith.rnote.com/api/sns/v1/system_service/splash_config',
          '优酷':'https://un-acs.youku.com/gw/mtop.youku.play.ups.appinfo.get/1.0/',
          '爱奇艺':'https://t7z.cupid.iqiyi.com/mixer?platform=ios',
          '什么值得买':'https://app-api.smzdm.com/util/loading',
          '12306':'https://ad.12306.cn/ad/ser/getAdList',
          '美团 & 美团外卖':'https://wmapi.meituan.com/api/v7/startpicture?platform=ios',
          '中国联通':'https://m.client.10010.com/uniAdmsInterface/getWelcomeAd',
          '腾讯视频':'https://splashqqlive.gtimg.com/a.jpg',
          '墨迹天气':'https://adlaunch.moji.com/a',
        }
        for app,url in cases.items():
            with self.subTest(app=app):
                self.assertEqual(self.hit(rows,url)['app'],app)

    def test_new_simple_startup_rule_on_prereviewed_app_host_is_automatic(self):
        text='#!name=fixture\n[Map Local]\n# > 夸克\n^https://open-cms-api\\.quark\\.cn/splash_v7 data-type=text data="{}" header="Content-Type:application/json"'
        # Registry membership is reviewed beforehand, never inferred from a URL name.
        self.assertIn('open-cms-api.quark.cn', POLICY['auto_update_hosts']['夸克'])
        rows,_=sync.select_rules(text,POLICY)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['selection'],'bounded-upstream-update')
        self.assertTrue(re.search(rows[0]['pattern'],'https://open-cms-api.quark.cn/splash_v7?platform=ios'))
        self.assertFalse(re.search(rows[0]['pattern'],'https://open-cms-api.quark.cn/splash_v7_settings'))

    def test_unknown_host_or_mixed_config_cannot_enter_through_auto_registry(self):
        for pattern in (r'^https://new-unknown\.quark\.cn/splash_v7', r'^https://open-cms-api\.quark\.cn/splash/config'):
            text='#!name=fixture\n[Map Local]\n# > 夸克\n'+pattern+' data-type=text data="{}" header="Content-Type:application/json"'
            rows,_=sync.select_rules(text,POLICY)
            self.assertEqual(rows,[])

    def test_native_host_rules_are_exact_and_do_not_add_mitm(self):
        rows=selected_fixture_rows()
        domains=[r for r in rows if r['section']=='Rule']
        self.assertEqual(len(domains),15)
        self.assertTrue(all(r['hosts']==[] for r in domains))
        for row in domains:
            self.assertIsNone(self.hit(rows,'https://child.'+row['pattern']+'/normal'))
            self.assertIsNone(self.hit(rows,'https://normal.example/path?host='+row['pattern']))
        module=sync.render_module(rows,'osuphi/shadowrocket-startup-ads','main','fixture')
        self.assertNotIn('[Script]',module)
        self.assertNotIn('DOMAIN-SUFFIX,',module.split('[Rule]')[1].split('[URL Rewrite]')[0])

    def test_coverage_catalog_does_not_inflate_app_labels_into_device_results(self):
        report,_=sync.coverage_report(selected_fixture_rows(),POLICY,'')
        apps=report['apps']
        self.assertEqual(len(apps),77)
        self.assertEqual(len({v['app'] for v in apps}),77)
        self.assertTrue(all(not v['device_tested'] for v in apps))
        self.assertGreater(next(v for v in apps if v['app']=='淘宝')['active_rule_count'],0)
        self.assertTrue(all('etao' not in r['pattern'] for r in selected_fixture_rows() if r['app']=='淘宝'))
        self.assertGreater(next(v for v in apps if v['app']=='一淘')['active_rule_count'],0)
        self.assertEqual(next(v for v in apps if v['app']=='中国广电')['active_rule_count'],0)

    def test_all_new_body_transforms_preserve_unrelated_response_fields(self):
        jq=shutil.which('jq')
        if not jq:
            if os.environ.get('REQUIRE_JQ')=='1':self.fail('jq is mandatory before publication')
            self.skipTest('cloud executes real jq; jq is unavailable locally')
        cases=[
          ('jd-start',{'code':0,'images':[1],'showTimesDaily':5,'keep':7},{'code':0,'images':[],'showTimesDaily':0,'keep':7}),
          ('xhs-splash',{'code':0,'data':{'ads_groups':[1],'splash':{'ad':1},'loading_img':'ad','app_theme':'normal','store':{'normal':1},'login':1}},{'code':0,'data':{'ads_groups':[],'app_theme':'normal','store':{'normal':1},'login':1}}),
          ('iqiyi-ad',{'errorCode':0,'adSlots':[1],'splashLottieFile':'ad','splashUiConfig':{},'keep':7},{'errorCode':0,'keep':7}),
          ('youku-ad',{'code':0,'data':{'data':{'ad':1,'ykad':2,'watermark':'original','stream':{'video':1},'user':{'status':'unchanged'}}}},{'code':0,'data':{'data':{'watermark':'original','stream':{'video':1},'user':{'status':'unchanged'}}}}),
          ('smzdm-loading',{'code':0,'data':{'splash':1},'message':'ok'},{'code':0,'message':'ok'}),
          ('rail-ad',{'code':'00','materialsList':[{'filePath':'ad'}],'advertParam':{'skipTime':5,'keep':7},'message':'ok'},{'code':'00','materialsList':[],'advertParam':{'skipTime':0,'keep':7},'message':'ok'}),
          ('luckin-ad',{'status':'SUCCESS','data':{'ad':1}},{'status':'SUCCESS'}),
        ]
        taobao={'ret':['SUCCESS'],'data':{'containers':{'splash_home_base':{'base':{'sections':[{'bizData':{'taobao-splash':{'data':[{'imgUrl':'ad'}],'keep':7},'ordinary-product':{'data':[1,2,3]}}}]}}}}}
        expected=copy.deepcopy(taobao)
        expected['data']['containers']['splash_home_base']['base']['sections'][0]['bizData']['taobao-splash']['data']=[]
        cases.append(('taobao-splash',taobao,expected))
        for key,value,expected in cases:
            for original,wanted in [(value,expected),(None,None),([],[]),('unsupported','unsupported')]:
                with self.subTest(transform=key,input=original):
                    result=subprocess.run([jq,'-c',sync.BODY_TRANSFORMS[key]],input=json.dumps(original),capture_output=True,text=True,check=True)
                    self.assertEqual(json.loads(result.stdout),wanted)


if __name__=='__main__':unittest.main()
