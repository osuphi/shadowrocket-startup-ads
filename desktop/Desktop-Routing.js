// Desktop routing extension v4 — FlClash / Clash Verge Rev.
// Import as a SCRIPT attached to an existing subscription; this is not a node subscription.
// Synchronous main(config) is shared by both clients. No network, filesystem, or host APIs.
// Existing proxies, proxy-providers, DNS, ports, TUN, and other settings remain in the local app.
// Only routing rules and this extension's groups/rule-providers are generated here.
// Disable this extension to return to the subscription's routing on its next application.
// HTTP rule-provider contents refresh daily while the core runs. This local JS does not self-update.

function main(config) {
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("请把脚本挂到已有节点订阅的扩展脚本中。");
  }
  const spec = {
  "version": 4,
  "prefix": "精细分流 · ",
  "providerPrefix": "fine-bm7-",
  "groups": {
    "Bark": "精细分流 · Bark",
    "🔰 选择节点": "精细分流 · 节点选择",
    "🤖 OpenAI": "精细分流 · OpenAI",
    "▶️ YouTube": "精细分流 · YouTube",
    "🔎 Google": "精细分流 · Google",
    "🐙 GitHub": "精细分流 · GitHub",
    "🍎 Apple 海外": "精细分流 · Apple 海外",
    "💬 Bing / Copilot": "精细分流 · Bing / Copilot",
    "☁️ OneDrive": "精细分流 · OneDrive",
    "🎮 Steam 商店/社区": "精细分流 · Steam 商店/社区",
    "🌩️ Cloudflare": "精细分流 · Cloudflare",
    "🪟 Microsoft": "精细分流 · Microsoft",
    "🍎 Apple": "精细分流 · Apple",
    "🪟 微软下载": "精细分流 · 微软下载",
    "🎮 Steam 登录/下载": "精细分流 · Steam 登录/下载",
    "🌏 爱奇艺&哔哩哔哩": "精细分流 · 爱奇艺&哔哩哔哩",
    "📺 动画疯": "精细分流 · 动画疯",
    "🎓学术网站": "精细分流 · 学术网站",
    "🇨🇳 国内网站": "精细分流 · 国内网站",
    "🛑 拦截广告": "精细分流 · 拦截广告",
    "🐟 漏网之鱼": "精细分流 · 漏网之鱼",
    "📺 国内直播": "精细分流 · 国内直播",
    "💬 国内通讯": "精细分流 · 国内通讯",
    "💳 国内支付": "精细分流 · 国内支付",
    "📱 运营商服务": "精细分流 · 运营商服务"
  },
  "directGroups": [
    "🍎 Apple",
    "🪟 微软下载",
    "🎮 Steam 登录/下载",
    "🌏 爱奇艺&哔哩哔哩",
    "🎓学术网站",
    "🇨🇳 国内网站",
    "📺 国内直播",
    "💬 国内通讯",
    "💳 国内支付",
    "📱 运营商服务"
  ],
  "proxyGroups": [
    "🤖 OpenAI",
    "▶️ YouTube",
    "🔎 Google",
    "🐙 GitHub",
    "🍎 Apple 海外",
    "💬 Bing / Copilot",
    "☁️ OneDrive",
    "🎮 Steam 商店/社区",
    "🌩️ Cloudflare",
    "🪟 Microsoft",
    "📺 动画疯"
  ],
  "regions": [
    {
      "name": "精细分流 · 香港节点",
      "pattern": "香港|Hong[ -]?Kong|(?:^|[^A-Za-z])HK(?:[^A-Za-z]|$)|🇭🇰"
    },
    {
      "name": "精细分流 · 日本节点",
      "pattern": "日本|东京|大阪|Japan|Tokyo|(?:^|[^A-Za-z])JP(?:[^A-Za-z]|$)|🇯🇵"
    },
    {
      "name": "精细分流 · 新加坡节点",
      "pattern": "新加坡|狮城|Singapore|(?:^|[^A-Za-z])SG(?:[^A-Za-z]|$)|🇸🇬"
    },
    {
      "name": "精细分流 · 美国节点",
      "pattern": "美国|洛杉矶|圣何塞|西雅图|United[ -]?States|USA|(?:^|[^A-Za-z])US(?:[^A-Za-z]|$)|🇺🇸|🇺🇲"
    },
    {
      "name": "精细分流 · 台湾节点",
      "pattern": "台湾|台灣|台北|Taiwan|Taipei|(?:^|[^A-Za-z])TW(?:[^A-Za-z]|$)|🇹🇼"
    }
  ],
  "providers": {
    "fine-bm7-AppleProxy": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/AppleProxy.list",
      "path": "./ruleset/fine-precision/AppleProxy.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Apple": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Apple.list",
      "path": "./ruleset/fine-precision/Apple.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-AliPay": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/AliPay.list",
      "path": "./ruleset/fine-precision/AliPay.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-UnionPay": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/UnionPay.list",
      "path": "./ruleset/fine-precision/UnionPay.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-WeChat": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/WeChat.list",
      "path": "./ruleset/fine-precision/WeChat.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-DingTalk": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/DingTalk.list",
      "path": "./ruleset/fine-precision/DingTalk.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-ChinaMobile": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/ChinaMobile.list",
      "path": "./ruleset/fine-precision/ChinaMobile.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-ChinaTelecom": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/ChinaTelecom.list",
      "path": "./ruleset/fine-precision/ChinaTelecom.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-ChinaUnicom": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/ChinaUnicom.list",
      "path": "./ruleset/fine-precision/ChinaUnicom.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Douyu": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Douyu.list",
      "path": "./ruleset/fine-precision/Douyu.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-HuYa": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/HuYa.list",
      "path": "./ruleset/fine-precision/HuYa.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-BiliBili": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/BiliBili.list",
      "path": "./ruleset/fine-precision/BiliBili.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-iQIYI": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/iQIYI.list",
      "path": "./ruleset/fine-precision/iQIYI.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-SteamCN": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/SteamCN.list",
      "path": "./ruleset/fine-precision/SteamCN.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-ConservativeAds": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/ads/ConservativeAds.list",
      "path": "./ruleset/fine-precision/ConservativeAds.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-OpenAI": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/OpenAI.list",
      "path": "./ruleset/fine-precision/OpenAI.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-YouTube": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/YouTube.list",
      "path": "./ruleset/fine-precision/YouTube.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Google": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Google.list",
      "path": "./ruleset/fine-precision/Google.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-GitHub": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/GitHub.list",
      "path": "./ruleset/fine-precision/GitHub.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-OneDrive": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/OneDrive.list",
      "path": "./ruleset/fine-precision/OneDrive.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Bing": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Bing.list",
      "path": "./ruleset/fine-precision/Bing.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Microsoft": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Microsoft.list",
      "path": "./ruleset/fine-precision/Microsoft.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Steam": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Steam.list",
      "path": "./ruleset/fine-precision/Steam.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-Bahamut": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/Bahamut.list",
      "path": "./ruleset/fine-precision/Bahamut.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    },
    "fine-bm7-China": {
      "type": "http",
      "behavior": "classical",
      "format": "text",
      "url": "https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/routing/lists/China.list",
      "path": "./ruleset/fine-precision/China.list",
      "interval": 86400,
      "proxy": "精细分流 · 节点选择"
    }
  },
  "rules": [
    "DOMAIN,api.day.app,精细分流 · Bark",
    "DOMAIN,localhost,DIRECT",
    "DOMAIN-SUFFIX,local,DIRECT",
    "DOMAIN,captive.apple.com,DIRECT",
    "IP-CIDR,0.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
    "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,224.0.0.0/4,DIRECT,no-resolve",
    "IP-CIDR,255.255.255.255/32,DIRECT,no-resolve",
    "IP-CIDR6,::1/128,DIRECT,no-resolve",
    "IP-CIDR6,fc00::/7,DIRECT,no-resolve",
    "IP-CIDR6,fe80::/10,DIRECT,no-resolve",
    "IP-CIDR6,ff00::/8,DIRECT,no-resolve",
    "DOMAIN,cable.auth.com,DIRECT",
    "DOMAIN,app-site-association.cdn-apple.com,DIRECT",
    "DOMAIN,app-site-association.networking.apple,DIRECT",
    "DOMAIN-SUFFIX,push.apple.com,DIRECT",
    "DOMAIN,raw.githubusercontent.com,精细分流 · GitHub",
    "DOMAIN,challenges.cloudflare.com,精细分流 · 节点选择",
    "DOMAIN,js.stripe.com,精细分流 · 节点选择",
    "DOMAIN,api.stripe.com,精细分流 · 节点选择",
    "DOMAIN,checkout.stripe.com,精细分流 · 节点选择",
    "DOMAIN,hooks.stripe.com,精细分流 · 节点选择",
    "DOMAIN,openai-api.arkoselabs.com,精细分流 · OpenAI",
    "DOMAIN-SUFFIX,auth0.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,client-api.arkoselabs.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,hcaptcha.com,精细分流 · 节点选择",
    "DOMAIN,browser-intake-datadoghq.com,精细分流 · 节点选择",
    "DOMAIN,static.cloudflareinsights.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,ai.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,algolia.net,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,api.statsig.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,events.statsigapi.net,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,featuregates.org,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,host.livekit.cloud,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,identrust.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,intercom.io,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,intercomcdn.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,launchdarkly.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,observeit.net,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,segment.io,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,sentry.io,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,stripe.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,turn.livekit.cloud,精细分流 · 节点选择",
    "DOMAIN,firebaseinstallations.googleapis.com,精细分流 · Google",
    "DOMAIN,firebaseremoteconfig.googleapis.com,精细分流 · Google",
    "DOMAIN,firebase-settings.crashlytics.com,精细分流 · Google",
    "DOMAIN,fcm.googleapis.com,精细分流 · Google",
    "DOMAIN-SUFFIX,sentry-cdn.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,crashlytics.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,app-measurement.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,firebaseio.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,firebaseapp.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,statsig.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,statsigapi.net,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,configcat.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,split.io,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,segment.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,mixpanel.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,mparticle.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,optimizely.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,onesignal.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,pusher.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,pushwoosh.com,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,recaptcha.net,精细分流 · 节点选择",
    "DOMAIN-SUFFIX,bugly.qq.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,sensorsdata.cn,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,sensorsdata.io,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,umeng.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,umeng.co,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,umengcloud.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,umengacs.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,cmpassport.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,id6.me,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,onepass.geetest.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,geetest.com,精细分流 · 国内网站",
    "DOMAIN-SUFFIX,gtimg.com,精细分流 · 国内网站",
    "RULE-SET,fine-bm7-AppleProxy,精细分流 · Apple 海外",
    "RULE-SET,fine-bm7-Apple,精细分流 · Apple",
    "RULE-SET,fine-bm7-AliPay,精细分流 · 国内支付",
    "RULE-SET,fine-bm7-UnionPay,精细分流 · 国内支付",
    "RULE-SET,fine-bm7-WeChat,精细分流 · 国内通讯",
    "RULE-SET,fine-bm7-DingTalk,精细分流 · 国内通讯",
    "RULE-SET,fine-bm7-ChinaMobile,精细分流 · 运营商服务",
    "RULE-SET,fine-bm7-ChinaTelecom,精细分流 · 运营商服务",
    "RULE-SET,fine-bm7-ChinaUnicom,精细分流 · 运营商服务",
    "RULE-SET,fine-bm7-Douyu,精细分流 · 国内直播",
    "RULE-SET,fine-bm7-HuYa,精细分流 · 国内直播",
    "RULE-SET,fine-bm7-BiliBili,精细分流 · 爱奇艺&哔哩哔哩",
    "RULE-SET,fine-bm7-iQIYI,精细分流 · 爱奇艺&哔哩哔哩",
    "RULE-SET,fine-bm7-SteamCN,精细分流 · Steam 登录/下载",
    "DOMAIN-SUFFIX,10099.com.cn,精细分流 · 运营商服务",
    "RULE-SET,fine-bm7-ConservativeAds,精细分流 · 拦截广告",
    "DOMAIN-SUFFIX,copilot.microsoft.com,精细分流 · Bing / Copilot",
    "DOMAIN-SUFFIX,copilot.cloud.microsoft,精细分流 · Bing / Copilot",
    "DOMAIN-SUFFIX,githubcopilot.com,精细分流 · GitHub",
    "DOMAIN,download.microsoft.com,精细分流 · 微软下载",
    "DOMAIN,ntservicepack.microsoft.com,精细分流 · 微软下载",
    "DOMAIN-SUFFIX,dl.delivery.mp.microsoft.com,精细分流 · 微软下载",
    "DOMAIN-SUFFIX,update.microsoft.com,精细分流 · 微软下载",
    "DOMAIN-SUFFIX,windowsupdate.microsoft.com,精细分流 · 微软下载",
    "DOMAIN-SUFFIX,windowsupdate.com,精细分流 · 微软下载",
    "RULE-SET,fine-bm7-OpenAI,精细分流 · OpenAI",
    "RULE-SET,fine-bm7-YouTube,精细分流 · YouTube",
    "RULE-SET,fine-bm7-Google,精细分流 · Google",
    "RULE-SET,fine-bm7-GitHub,精细分流 · GitHub",
    "RULE-SET,fine-bm7-OneDrive,精细分流 · OneDrive",
    "RULE-SET,fine-bm7-Bing,精细分流 · Bing / Copilot",
    "RULE-SET,fine-bm7-Microsoft,精细分流 · Microsoft",
    "RULE-SET,fine-bm7-Steam,精细分流 · Steam 商店/社区",
    "RULE-SET,fine-bm7-Bahamut,精细分流 · 动画疯",
    "DOMAIN-SUFFIX,webofscience.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,sciencedirect.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,webofknowledge.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,clarivate.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,taylorandfrancis.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,dl.acm.org,精细分流 · 学术网站",
    "DOMAIN,acm-prod.disqus.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,sciencedirectassets.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,readspeaker.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,pubmed.ncbi.nlm.nih.gov,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,ieee.org,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,nature.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,elsevier.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,tandfonline.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,springer.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,onlinelibrary.wiley.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,taylorfrancis.com,精细分流 · 学术网站",
    "DOMAIN-SUFFIX,cloudflare-dns.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflare-ipfs.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflare-quic.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflare.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflare.net,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflareapps.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflarebolt.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflareclient.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflareinsights.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflareok.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflareresolve.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflaressl.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflarestatus.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflarestream.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflaretest.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,cloudflarewarp.com,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,one.one.one,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,pages.dev,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,videodelivery.net,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,warp.plus,精细分流 · Cloudflare",
    "DOMAIN-SUFFIX,workers.dev,精细分流 · Cloudflare",
    "RULE-SET,fine-bm7-China,精细分流 · 国内网站",
    "GEOIP,CN,精细分流 · 国内网站",
    "MATCH,精细分流 · 漏网之鱼"
  ]
};
  const result = JSON.parse(JSON.stringify(config));
  const originalProxies = Array.isArray(result.proxies) ? result.proxies : [];
  const proxyProviders = result["proxy-providers"] || {};
  const providerNames = Object.keys(proxyProviders);
  const notices = "剩余|到期|套餐|流量|官网|客服|过期|Traffic|Expire|Expired|Reset|Official|https?://";
  const noticeRegex = new RegExp(notices, "i");
  const builtins = ["DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE", "GLOBAL"];
  const realNames = [];
  const seen = Object.create(null);
  for (const proxy of originalProxies) {
    if (!proxy || typeof proxy.name !== "string" || !proxy.name) continue;
    if (seen[proxy.name]) throw new Error("订阅里有重复节点名称，请先修复原订阅。");
    seen[proxy.name] = true;
    if (proxy.name.indexOf(spec.prefix) === 0) throw new Error("节点名与本扩展的分组前缀冲突。");
    const type = String(proxy.type || "").toLowerCase();
    if (builtins.indexOf(proxy.name) >= 0 || ["direct", "reject", "dns", "pass"].indexOf(type) >= 0) continue;
    if (!noticeRegex.test(proxy.name)) realNames.push(proxy.name);
  }
  if (realNames.length === 0 && providerNames.length === 0) {
    throw new Error("原配置没有可用的节点定义或节点集合。请先添加节点订阅。");
  }

  const g = spec.groups;
  const primary = g["🔰 选择节点"];
  const fresh = [];
  function select(name, choices) {
    const unique = [];
    for (const choice of choices) if (unique.indexOf(choice) < 0) unique.push(choice);
    fresh.push({ name: name, type: "select", proxies: unique });
  }
  // A refreshed subscription rebuilds this list; no node labels or private URLs are in this file.
  const mainGroup = { name: primary, type: "select", "empty-fallback": "REJECT" };
  if (realNames.length) mainGroup.proxies = realNames;
  if (providerNames.length) {
    mainGroup.use = providerNames;
    mainGroup["exclude-filter"] = "(?i)" + notices;
  }
  fresh.push(mainGroup);

  const regions = [];
  for (const region of spec.regions) {
    const regex = new RegExp(region.pattern, "i");
    const matches = realNames.filter(function (name) { return regex.test(name); });
    if (matches.length === 0 && providerNames.length === 0) continue;
    const group = {
      name: region.name, type: "select", proxies: matches.concat([primary]),
      "empty-fallback": "REJECT"
    };
    if (providerNames.length) {
      group.use = providerNames;
      group.filter = "(?i)" + region.pattern;
      group["exclude-filter"] = "(?i)" + notices;
    }
    fresh.push(group);
    regions.push(region.name);
  }

  for (const key of spec.proxyGroups) {
    select(g[key], [primary].concat(regions, ["DIRECT"]));
  }
  for (const key of spec.directGroups) {
    select(g[key], ["DIRECT", primary]);
  }
  select(g["🛑 拦截广告"], ["REJECT", primary, "DIRECT"]);
  select(g["🐟 漏网之鱼"], [primary, "DIRECT"]);
  // Bark can select its own node, including nodes loaded by the subscription providers.
  fresh.push(Object.assign({}, mainGroup, {
    name: g.Bark,
    proxies: [primary, "DIRECT"].concat(realNames)
  }));

  // Retain ALL legacy groups: node/provider dialer-proxy or detour references may depend on them.
  // A second run replaces only our own namespace, so applying this script twice is safe.
  const previousGroups = Array.isArray(result["proxy-groups"]) ? result["proxy-groups"] : [];
  const legacyGroups = previousGroups.filter(function (group) {
    return group && typeof group.name === "string" && group.name.indexOf(spec.prefix) !== 0;
  });
  result["proxy-groups"] = fresh.concat(legacyGroups);

  const ruleProviders = result["rule-providers"] || {};
  // Legacy providers are retained because existing sub-rules can still reference them.
  for (const name of Object.keys(ruleProviders)) {
    if (name.indexOf(spec.providerPrefix) === 0) delete ruleProviders[name];
  }
  for (const name of Object.keys(spec.providers)) ruleProviders[name] = spec.providers[name];
  result["rule-providers"] = ruleProviders;
  result.rules = spec.rules.slice();
  return result;
}
