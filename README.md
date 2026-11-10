# Shadowrocket 开屏广告增强：自动同步筛选版

> 新增：[Shadowrocket Precision v3 分流配置](routing/README.md)。这是独立的完整分流配置，包含保守广告过滤和国内服务分类；原有开屏模块的订阅地址继续保留。

基于 [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 的公开规则生成，保留原作者和贡献者署名，以 GPL-3.0 提供。模块修订：2026-11-11.1。

本项目提供独立的 Shadowrocket 模块，叠加在原有分流配置上。没有节点订阅、证书或密码；不会替换你的节点配置。

## 安装模块

当前部署的订阅地址：[StartupAds.module](https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/StartupAds.module)。复制这个链接地址到 Shadowrocket，不要把整个 GitHub 仓库地址填进模块订阅。

公开部署后，在 Shadowrocket“配置 → 模块 → 右上角 +”中填入本仓库 `StartupAds.module` 的 Raw 地址，下载并启用。不要复制 GitHub 的网页预览地址。

如果安装过旧的本地“开屏广告增强”模块，先停用旧版，再启用这份远程模块。分流可使用上方 Precision v3；如果之前导入了内置同一套开屏规则的完整增强 `.conf`，不要再重复叠加同一模块。WLOC 是独立定位模块。

本模块要求 Shadowrocket 2.2.69 或以上。需要对正在使用的配置开启 HTTPS 解密，并使用已在本机安装、完全信任的个人 CA。模块只追加指定主机名，不附带证书，也不会自动开启解密。

已安装并信任的个人 CA 可以复用。本次修订沿用同一订阅地址，只更新现有模块；不需要重新生成证书，也不需要重新导入主配置。哔哩哔哩和知乎使用客户端原生 `http-response-jq` 正文改写；旧客户端若不支持该功能，需要更新客户端。

解密按主机发生，这些主机上的正常请求也可能由客户端在本机解密；仅列出的开屏请求被改写/拒绝。WLOC 的定位域名不在本模块范围内。不能保证所有 App 或所有版本均去除开屏广告，缓存、证书固定和混合响应仍有局限。

## 自动更新分两步

1. 仓库里的 GitHub Actions 每天北京时间约 09:23 检查公开上游，筛选、校验并更新模块；也支持手动运行。
2. 在 Shadowrocket“设置 → 模块”中开启“自动后台更新”，间隔可选 1 天，并允许 iOS“后台 App 刷新”。手机会刷新这个固定地址的模块。

两边的调度都不保证准确时刻，iOS 强制结束应用或 GitHub 暂停定时任务会影响更新。安装后可以在 `UpdateStatus.json` 查看上次检查时间、上游日期、规则数和筛选结果。

Shadowrocket 模块与后台更新设置参考 [LOWERTOP 社区手册](https://github.com/LOWERTOP/Shadowrocket/wiki#自动更新)，该文档不是开发商官方文档。GitHub 定时机制参考 [GitHub Actions 官方说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 同步范围

初始版本含 104 条规则，但缺少哔哩哔哩、斗鱼、微博的开屏处理，知乎仅返回空响应，覆盖与兼容性不足。2026-11-11.1 修订改为 108 条，包含 102 个上游 App 标签、127 个精确主机名。标签不等于所有当前 App 版本已经实测。

本次重点修订：

- 哔哩哔哩：仅匹配 `app.bilibili.com/x/v2/splash/` 下的 list、show、event/list2，保留响应状态及其他字段，仅清空开屏展示数组。普通视频、直播、账号和会员接口不匹配。
- 斗鱼：仅匹配 `rtbapi.douyucdn.cn/japi/sign/app/getinfo` 并返回空 JSON；不恢复整域拦截，不处理直播清晰度、播放或检查更新接口。
- 微博：从同作者的独立 `weibo.srmodule` 中筛选两个明确开屏端点：bootpreload 和 bootrealtime。普通消息、推送、信息流、日志和整域封禁规则不加入。
- 知乎：已有 launch_v2 和 real_time_launch_v2 改为保留响应结构，仅将 `img_play_duration`、`launch_timeout` 清零；嵌套 JSON 字符串保持字符串类型。普通推荐流、答案、账号及云配置不处理。

这些是针对上游已知接口的修订，不是对所有当前 App 版本的实测保证。缓存广告、实际使用其他接口、证书固定或客户端未成功改写时，仍可能显示开屏。不能据此声称所有广告已经消失。

- 已逐项审阅的规则按收窄后的版本保留，避免重新加入腾讯新闻普通配置、知乎普通内容等混合接口。
- 自动接收已审阅应用、已审阅主机上的明确新开屏接口；保留上游支持的拒绝、空文本/空 JSON 或透明小图响应。
- 新主机名、新应用、混合业务路径、初始化/DNS/账户接口、远程执行脚本、正文/请求头改写等不自动加入，留待明确审阅。本次两个正文改写属于人工加入、固定白名单的原生 jq 表达式；不会自动执行任意新上游表达式。这样不会因上游变动而静默扩大证书解密范围。
- 检查正常登录、用户资料、订单、支付和 WLOC 路径不被捕获。检测到异常、下载失败或规则数量大幅下降时，停止发布，保留上一次仓库里的模块。
- 上游退休的旧开屏路径会记录在状态中，不会因此阻止其他正常规则更新。

这能减少日常名单维护，但不承诺永远免维护。上游格式变化、客户端语法变化、新应用或新主机仍可能需要调整。

## 运行方式

工作流使用 GitHub 自带的临时令牌，仅授予当前仓库内容写入权限，不需要填写个人密码或 Token。Python 只解析公开文本，不执行上游脚本。两个 GitHub 官方 Action 均固定到已核对的提交摘要。

本地维护者可以运行：

```sh
REQUIRE_JQ=1 python -m unittest -v test_sync.py test_focus_apps.py
python sync_module.py --repository OWNER/REPOSITORY --branch main
```

`reviewed_rules.json` 保存审阅过的原规则、收窄输出和允许的主机范围；`sync_module.py` 是可编辑生成器，`StartupAds.module` 是生成结果。源代码、模块和许可证随仓库提供。

发布环境必须提供 jq，并真正执行哔哩哔哩及知乎的响应夹具测试：正常字段、响应结构、异常响应和嵌套 JSON 字符串不得被破坏。另有 52 个已知请求匹配场景，包括 29 个正常/保护请求。任一检查失败不会发布本次新模块。首次修订在本地缺少 jq 时会明确跳过两项表达式执行测试；云端发布要求全部执行，不允许跳过。

云端会定期检查两份公开上游，但“检查成功”不等于“规则有新增”。状态中的 `module_changed`、`module_sha256` 和 `revision` 可用于区分；若上游没变化或变动超出审核范围，输出可以保持不变。手机自动后台更新需要另外开启，且 iOS/GitHub 调度可能延迟。

## 排查与恢复

App 异常时先停用本模块，保留原分流配置即可。要停止自动同步，可在 GitHub Actions 禁用工作流；手机端也可单独停用模块更新。

本项目未在 iPhone 上逐 App 实测，也未承诺原生导入、TLS 和所有真实定时更新成功。发布者应先确认第一次 Actions 执行成功，再在手机导入。

## 许可

GNU GPL v3，见 `LICENSE`。原作者 fmz200 及贡献者；本项目是筛选与自动生成的修改版，不是原完整合集。无担保。
