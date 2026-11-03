# Shadowrocket 开屏广告增强：自动同步筛选版

> 新增：[Shadowrocket Precision v3 分流配置](routing/README.md)。这是独立的完整分流配置，包含保守广告过滤和国内服务分类；原有开屏模块的订阅地址继续保留。

基于 [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 的公开规则生成，保留原作者和贡献者署名，以 GPL-3.0 提供。修改于 2026-11-02。

本项目提供独立的 Shadowrocket 模块，叠加在原有分流配置上。没有节点订阅、证书或密码；不会替换你的节点配置。

## 安装模块

当前部署的订阅地址：[StartupAds.module](https://raw.githubusercontent.com/osuphi/shadowrocket-startup-ads/main/StartupAds.module)。复制这个链接地址到 Shadowrocket，不要把整个 GitHub 仓库地址填进模块订阅。

公开部署后，在 Shadowrocket“配置 → 模块 → 右上角 +”中填入本仓库 `StartupAds.module` 的 Raw 地址，下载并启用。不要复制 GitHub 的网页预览地址。

如果安装过旧的本地“开屏广告增强”模块，先停用旧版，再启用这份远程模块。建议继续使用原有的 v2 分流配置；如果之前导入了内置同一套开屏规则的完整增强 `.conf`，先切回 v2，避免重复叠加。WLOC 是独立定位模块。

本模块要求 Shadowrocket 2.2.69 或以上。需要对正在使用的配置开启 HTTPS 解密，并生成、安装和完全信任你自己的 CA。模块只追加指定主机名，不附带证书，也不会自动开启解密。

解密按主机发生，这些主机上的正常请求也可能由客户端在本机解密；仅列出的开屏请求被改写/拒绝。WLOC 的定位域名不在本模块范围内。不能保证所有 App 或所有版本均去除开屏广告，缓存、证书固定和混合响应仍有局限。

## 自动更新分两步

1. 仓库里的 GitHub Actions 每天北京时间约 09:23 检查公开上游，筛选、校验并更新模块；也支持手动运行。
2. 在 Shadowrocket“设置 → 模块”中开启“自动后台更新”，间隔可选 1 天，并允许 iOS“后台 App 刷新”。手机会刷新这个固定地址的模块。

两边的调度都不保证准确时刻，iOS 强制结束应用或 GitHub 暂停定时任务会影响更新。安装后可以在 `UpdateStatus.json` 查看上次检查时间、上游日期、规则数和筛选结果。

Shadowrocket 模块与后台更新设置参考 [LOWERTOP 社区手册](https://github.com/LOWERTOP/Shadowrocket/wiki#自动更新)，该文档不是开发商官方文档。GitHub 定时机制参考 [GitHub Actions 官方说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 同步范围

初始版本含 104 条开屏接口规则，来自 99 个上游 App 标签、123 个精确主机名。标签不等于所有当前 App 版本已经实测。

- 已逐项审阅的规则按收窄后的版本保留，避免重新加入腾讯新闻普通配置、知乎普通内容等混合接口。
- 自动接收已审阅应用、已审阅主机上的明确新开屏接口；保留上游支持的拒绝、空文本/空 JSON 或透明小图响应。
- 新主机名、新应用、混合业务路径、初始化/DNS/账户接口、远程执行脚本、正文/请求头改写等不自动加入，留待明确审阅。这样不会因上游变动而静默扩大证书解密范围。
- 检查正常登录、用户资料、订单、支付和 WLOC 路径不被捕获。检测到异常、下载失败或规则数量大幅下降时，停止发布，保留上一次仓库里的模块。
- 上游退休的旧开屏路径会记录在状态中，不会因此阻止其他正常规则更新。

这能减少日常名单维护，但不承诺永远免维护。上游格式变化、客户端语法变化、新应用或新主机仍可能需要调整。

## 运行方式

工作流使用 GitHub 自带的临时令牌，仅授予当前仓库内容写入权限，不需要填写个人密码或 Token。Python 只解析公开文本，不执行上游脚本。两个 GitHub 官方 Action 均固定到已核对的提交摘要。

本地维护者可以运行：

```sh
python -m unittest -v test_sync.py
python sync_module.py --repository OWNER/REPOSITORY --branch main
```

`reviewed_rules.json` 保存审阅过的原规则、收窄输出和允许的主机范围；`sync_module.py` 是可编辑生成器，`StartupAds.module` 是生成结果。源代码、模块和许可证随仓库提供。

## 排查与恢复

App 异常时先停用本模块，保留原分流配置即可。要停止自动同步，可在 GitHub Actions 禁用工作流；手机端也可单独停用模块更新。

本项目未在 iPhone 上逐 App 实测，也未承诺原生导入、TLS 和所有真实定时更新成功。发布者应先确认第一次 Actions 执行成功，再在手机导入。

## 许可

GNU GPL v3，见 `LICENSE`。原作者 fmz200 及贡献者；本项目是筛选与自动生成的修改版，不是原完整合集。无担保。
