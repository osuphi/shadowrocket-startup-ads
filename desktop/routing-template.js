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
  const spec = /*__PUBLIC_DATA__*/;
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
