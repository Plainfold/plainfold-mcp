#!/usr/bin/env python3
"""Generate everything from tools.json.

Usage: python3 scripts/build.py [path/to/plainfold.github.io]

Writes, in this repo: README.md, server.json (all tools), servers/<slug>/server.json.
Writes, in the site repo (if given): index.html, llms.txt, llms-full.txt, robots.txt, sitemap.xml.
To add a tool: add/complete its entry in tools.json, set "live": true, bump brand.combined.version, rerun.
"""
import datetime, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
DATA = json.load(open(os.path.join(ROOT, "tools.json"), encoding="utf-8"))
B = DATA["brand"]
TOOLS = [t for t in DATA["tools"] if t.get("live")]
SOON = [t for t in DATA["tools"] if not t.get("live")]
PRODUCTS = DATA.get("products", [])
TODAY = datetime.date.today().isoformat()


def mcp_url(slugs):
    return "https://mcp.apify.com/?tools=" + ",".join("plainfold/" + s for s in slugs)


def apify_url(t):
    return "https://apify.com/plainfold/" + t["slug"]


def tool_name(t):  # name the Apify MCP server gives the tool
    return "plainfold--" + t["slug"]


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


ALL_URL = mcp_url([t["slug"] for t in TOOLS])
AUTH_HEADER = {
    "name": "Authorization",
    "description": "Apify API token as 'Bearer <token>' (free account at apify.com). Optional if your MCP client supports OAuth sign-in.",
    "isRequired": False,
    "isSecret": True,
}
ICONS = [{"src": B["site"] + "/assets/plainfold-icon-512.png", "mimeType": "image/png", "sizes": ["512x512"]}]


def server_json(name, title, desc, version, url, website, subfolder=None):
    assert len(desc) <= 100, (name, len(desc))
    repo = {"url": B["repo"], "source": "github"}
    if B.get("repoId"):
        repo["id"] = str(B["repoId"])
    if subfolder:
        repo["subfolder"] = subfolder
    return {
        "$schema": SCHEMA,
        "name": name,
        "title": title,
        "description": desc,
        "version": version,
        "websiteUrl": website,
        "repository": repo,
        "icons": ICONS,
        "remotes": [{"type": "streamable-http", "url": url, "headers": [AUTH_HEADER]}],
    }


def build_servers():
    c = B["combined"]
    sj = server_json(f'{B["registryNamespace"]}/{c["slug"]}', c["title"], c["description"], c["version"], ALL_URL, B["site"])
    write(os.path.join(ROOT, "server.json"), json.dumps(sj, indent=2, ensure_ascii=False) + "\n")
    for t in TOOLS:
        sj = server_json(f'{B["registryNamespace"]}/{t["slug"]}', t["name"], t["registryDescription"], t["version"],
                         mcp_url([t["slug"]]), apify_url(t), subfolder=f'servers/{t["slug"]}')
        write(os.path.join(ROOT, "servers", t["slug"], "server.json"), json.dumps(sj, indent=2, ensure_ascii=False) + "\n")


def client_configs(key, url):
    cursor = {"mcpServers": {key: {"url": url, "headers": {"Authorization": "Bearer YOUR_APIFY_TOKEN"}}}}
    vscode = {"servers": {key: {"type": "http", "url": url}}}
    claude = {"mcpServers": {key: {"command": "npx", "args": ["-y", "mcp-remote", url, "--header", "Authorization:${AUTH_HEADER}"],
                                   "env": {"AUTH_HEADER": "Bearer YOUR_APIFY_TOKEN"}}}}
    return cursor, vscode, claude


def readme():
    L = []
    L.append('<p align="center"><img src="assets/plainfold-logo-light.png" alt="Plainfold" width="360"></p>\n')
    L.append("# Plainfold MCP tools\n")
    L.append(f'{B["tagline"]} Each tool runs on [Apify]({B["apifyProfile"]}) and is available to AI agents as a remote MCP server '
             "through Apify's hosted MCP endpoint. You pay per result, at the prices below. There's nothing to install or host.\n")
    L.append(f'Website: {B["site"]} · Machine-readable index: {B["site"]}/llms.txt\n')
    L.append("## Tools\n")
    L.append("| Tool | What it does | Price | MCP URL |\n|---|---|---|---|")
    for t in TOOLS:
        L.append(f'| [{t["name"]}]({apify_url(t)}) | {t["summary"]} | {t["priceShort"]} | `{mcp_url([t["slug"]])}` |')
    L.append(f'\nAll tools in one server: `{ALL_URL}`\n')
    if SOON:
        L.append("Coming soon: " + "; ".join(f'{t["name"]} ({t["summary"].rstrip(".")})' for t in SOON) + ".\n")
    L.append("## Quick start\n")
    L.append("1. Get an Apify account (free) at https://apify.com. MCP clients that support OAuth (Claude, VS Code, Cursor) "
             "can sign in to Apify in the browser, so you don't need to copy a token. Otherwise, copy your API token from "
             "https://console.apify.com/account/integrations.\n2. Add one of the URLs above to your MCP client (examples below).\n"
             "3. Ask your agent a question. It calls the tool, and the run is billed to your Apify account at the tool's price.\n")
    cursor, vscode, claude = client_configs("plainfold", ALL_URL)
    L.append("### Claude (claude.ai and Claude Desktop)\n")
    L.append(f"Settings → Connectors → **Add custom connector**, paste `{ALL_URL}` and sign in with Apify.\n")
    L.append("Or, in `claude_desktop_config.json`, using [mcp-remote](https://www.npmjs.com/package/mcp-remote) with a token:\n")
    L.append("```json\n" + json.dumps(claude, indent=2) + "\n```\n")
    L.append("### Claude Code\n")
    L.append(f'```bash\nclaude mcp add --transport http plainfold "{ALL_URL}"\n```\n')
    L.append("### Cursor (`~/.cursor/mcp.json`)\n")
    L.append("```json\n" + json.dumps(cursor, indent=2) + "\n```\n(Leave out `headers` to sign in with OAuth instead.)\n")
    L.append("### VS Code (`.vscode/mcp.json`)\n")
    L.append("```json\n" + json.dumps(vscode, indent=2) + "\n```\n")
    L.append("### Any other MCP client\n")
    L.append("Use streamable HTTP with the URL above and the header `Authorization: Bearer YOUR_APIFY_TOKEN`.\n")
    for t in TOOLS:
        L.append(f'## {t["name"]}\n')
        L.append(t["summary"] + "\n")
        L.extend(f"- {d}" for d in t["does"])
        L.append(f'\n**Use it for:** {t["useFor"]}  \n**Not for:** {t["notFor"]}  \n**Price:** {t["price"]}\n')
        L.append(f'- MCP URL: `{mcp_url([t["slug"]])}`\n- MCP tool name: `{tool_name(t)}`\n- Apify page and full docs: {apify_url(t)}\n'
                 f'- Registry entry: [`servers/{t["slug"]}/server.json`](servers/{t["slug"]}/server.json)\n')
        L.append(f'Example prompt: *"{t["examplePrompt"]}"*\n')
        L.append("Example MCP tool call:\n")
        L.append("```json\n" + json.dumps({"name": tool_name(t), "arguments": t["exampleInput"]}, indent=2) + "\n```\n")
        L.append("Or call it over plain HTTP (returns the results as JSON):\n")
        L.append("```bash\ncurl -X POST \"https://api.apify.com/v2/acts/plainfold~" + t["slug"] + "/run-sync-get-dataset-items\" \\\n"
                 "  -H \"Authorization: Bearer $APIFY_TOKEN\" -H \"Content-Type: application/json\" \\\n"
                 f"  -d '{json.dumps(t['exampleInput'])}'\n```\n")
    L.append("## AI agents without an Apify account\n")
    L.append("These tools are eligible for Apify's agentic payments, so an AI agent can run them and pay per use with "
             "[x402](https://docs.apify.com/platform/integrations/x402) or [Skyfire](https://docs.apify.com/platform/integrations/skyfire) instead of an Apify account.\n")
    L.append("## About\n")
    L.append(f'Plainfold is a tiny studio making guides, templates and small tools. Plain on purpose. We use official public data sources, never scrape behind logins, and never return personal data we don\'t need. '
             f'Questions or bugs: [open an issue]({B["repo"]}/issues).\n')
    L.append("This repo holds the docs and the [MCP Registry](https://registry.modelcontextprotocol.io) entries (`server.json`). "
             "The tools themselves run on Apify. Everything here is generated from `tools.json` by `scripts/build.py`.\n")
    L.append("License: MIT (this repo's docs and metadata).\n")
    write(os.path.join(ROOT, "README.md"), "\n".join(L))


# ---------------- site ----------------
CSS = """
:root{--navy:#1F2A44;--terra:#C4532D;--terra-text:#B04B28;--sand:#F4EDE4;--sand2:#EADFCF;--olive:#6B7F4F;--saffron:#E3A23B;--ink:#2A2F3A;--muted:#676B73}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--sand);color:var(--ink);font:17px/1.6 "Inter",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--terra-text)}a:hover{color:var(--navy)}
h1,h2,h3{font-family:"Fraunces",Georgia,serif;font-weight:600;color:var(--navy);line-height:1.15;margin:0 0 .4em}
h1{font-size:clamp(2.1rem,5vw,3.3rem)}h2{font-size:1.9rem;margin-top:0}h3{font-size:1.35rem}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
header.top{padding:28px 0}header.top img{height:40px;width:auto;display:block}
.hero{position:relative;overflow:hidden;padding:48px 0 64px}
.hero p.lede{font-size:1.2rem;max-width:620px;color:#444A56}
.hero .sub{font-family:"Fraunces",Georgia,serif;font-style:italic;color:var(--terra-text);font-size:1.3rem;margin:0 0 .6em}
.bar{width:72px;height:6px;background:var(--saffron);border-radius:3px;margin:18px 0 22px}
.mosaic{position:absolute;right:-40px;top:20px;display:grid;grid-template-columns:repeat(3,72px);gap:0;opacity:1}
.mosaic i{display:block;width:72px;height:72px}
.kicker{font-weight:700;text-transform:uppercase;letter-spacing:.16em;font-size:.8rem;color:var(--terra-text);margin:0 0 .5em}
section{padding:48px 0}section.alt{background:#fff}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px;margin-top:24px}
.card{background:#fff;border:1px solid var(--sand2);border-radius:14px;padding:24px 24px 18px}
section.alt .card{background:var(--sand)}
.card .price{display:inline-block;background:var(--navy);color:var(--sand);border-radius:999px;padding:3px 12px;font-size:.85rem;font-weight:600;margin:4px 0 12px}
.card ul{padding-left:1.1em;margin:.4em 0 1em}.card li{margin:.25em 0}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.85rem}
code{background:var(--sand2);padding:2px 6px;border-radius:5px;word-break:break-all}
pre{background:var(--navy);color:var(--sand);padding:14px 16px;border-radius:10px;overflow-x:auto}
.links a{margin-right:16px;font-weight:600}
.soon{color:var(--muted)}
.steps{counter-reset:s;list-style:none;padding:0}.steps li{counter-increment:s;margin:0 0 14px;padding-left:44px;position:relative}
.steps li:before{content:counter(s);position:absolute;left:0;top:0;width:30px;height:30px;border-radius:50%;background:var(--terra);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:.9rem}
footer{background:var(--navy);color:var(--sand);padding:36px 0;font-size:.95rem}footer a{color:var(--saffron)}
@media (max-width:720px){.mosaic{display:none}}
"""

MOSAIC = [("#C4532D", "50% 0 50% 0"), ("#1F2A44", "0"), ("#E3A23B", "50%"), ("#6B7F4F", "50% 50% 0 0"),
          ("#E3A23B", "0 50% 0 50%"), ("#C4532D", "0 0 50% 50%"), ("#1F2A44", "50%"), ("#C4532D", "0"), ("#6B7F4F", "50% 0 50% 0")]


def jsonld():
    org = {"@type": "Organization", "@id": B["site"] + "/#org", "name": B["name"], "url": B["site"] + "/",
           "logo": B["site"] + "/assets/plainfold-icon-512.png", "description": B["tagline"],
           "sameAs": [B["github"], B["apifyProfile"], B["x"], "https://plainfold.gumroad.com"]}
    items = []
    for t in TOOLS:
        items.append({"@type": "SoftwareApplication", "name": t["name"], "applicationCategory": "BusinessApplication",
                      "operatingSystem": "Web (API, MCP)", "url": apify_url(t), "description": t["summary"],
                      "publisher": {"@id": B["site"] + "/#org"},
                      "offers": [{"@type": "Offer", "name": o["name"], "price": o["price"], "priceCurrency": "USD"} for o in t["priceOffers"]]})
    for p in PRODUCTS:
        items.append({"@type": "Product", "name": p["name"], "url": p["url"], "description": p["summary"],
                      "brand": {"@id": B["site"] + "/#org"},
                      "offers": {"@type": "Offer", "price": p["price"], "priceCurrency": "USD", "url": p["url"], "availability": "https://schema.org/InStock"}})
    site = {"@type": "WebSite", "@id": B["site"] + "/#site", "url": B["site"] + "/", "name": B["name"], "publisher": {"@id": B["site"] + "/#org"}}
    lst = {"@type": "ItemList", "name": "Plainfold tools and products",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(items)]}
    return json.dumps({"@context": "https://schema.org", "@graph": [org, site, lst]}, indent=1, ensure_ascii=False)


def index_html():
    e = html.escape
    tiles = "".join(f'<i style="background:{c};border-radius:{r}"></i>' for c, r in MOSAIC)
    cards = []
    for t in TOOLS:
        cards.append(f'''<article class="card" id="{e(t["slug"])}">
<h3>{e(t["name"])}</h3><span class="price">{e(t["priceShort"])}</span>
<p>{e(t["summary"])}</p>
<ul>{"".join(f"<li>{e(d)}</li>" for d in t["does"][:3])}</ul>
<p><strong>Use it for:</strong> {e(t["useFor"])}</p>
<p>MCP URL:<br><code>{e(mcp_url([t["slug"]]))}</code></p>
<p class="links"><a href="{e(apify_url(t))}">Apify page &amp; docs</a><a href="{e(B["repo"])}#{e(t["name"].lower().replace(" ", "-").replace(".", ""))}">Setup</a></p>
</article>''')
    soon = ""
    if SOON:
        soon = '<p class="soon">Coming soon: ' + e("; ".join(f'{t["name"]}' for t in SOON)) + ".</p>"
    prods = "".join(f'''<article class="card"><h3>{e(p["name"])}</h3><span class="price">${e(p["price"])}</span>
<p>{e(p["summary"])}</p><p class="links"><a href="{e(p["url"])}">Get it on Gumroad</a></p></article>''' for p in PRODUCTS)
    desc = f'{B["tagline"]} Data tools for AI agents (MCP) and practical guides from Plainfold.'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plainfold: small, honest data tools for people and AI agents</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{B["site"]}/">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" href="/assets/favicon-32.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">
<meta property="og:type" content="website"><meta property="og:title" content="Plainfold"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{B["site"]}/"><meta property="og:image" content="{B["site"]}/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:site" content="@plainfoldco">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;1,9..144,400&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script type="application/ld+json">
{jsonld()}
</script>
</head>
<body>
<header class="top"><div class="wrap"><a href="/"><img src="/assets/plainfold-logo-light.svg" alt="Plainfold" width="188" height="40"></a></div></header>
<main>
<div class="hero"><div class="mosaic" aria-hidden="true">{tiles}</div><div class="wrap">
<p class="kicker">Guides, templates &amp; small tools</p>
<h1>Small, honest data tools<br>for people and AI agents</h1>
<p class="sub">Plain on purpose, never boring.</p>
<div class="bar"></div>
<p class="lede">Plainfold builds focused tools on official public data. AI agents can find them, run them and pay per result through MCP. People can use them too, with no code needed.</p>
<p class="links"><a href="#tools">See the tools</a><a href="#agents">Connect an agent</a><a href="/llms.txt">llms.txt</a></p>
</div></div>
<section id="tools" class="alt"><div class="wrap">
<p class="kicker">Data tools</p><h2>Tools for agents and people</h2>
<p>Each tool runs on Apify. You pay only for what you use, and there's no subscription.</p>
<div class="cards">{"".join(cards)}</div>{soon}
</div></section>
<section id="agents"><div class="wrap">
<p class="kicker">For AI agents</p><h2>Connect in a minute</h2>
<ol class="steps">
<li>Add this remote MCP server to Claude, Cursor, VS Code or any MCP client:<br><code>{e(ALL_URL)}</code></li>
<li>Sign in with a free Apify account (OAuth), or send <code>Authorization: Bearer YOUR_APIFY_TOKEN</code>.</li>
<li>Ask your question. Runs are billed per result at the prices above. Agents without an account can pay per use with x402 or Skyfire through Apify.</li>
</ol>
<p>Client-by-client setup, example calls and registry entries: <a href="{B["repo"]}">github.com/plainfold/plainfold-mcp</a>. Listed in the official <a href="https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.plainfold">MCP Registry</a> as <code>io.github.plainfold/*</code>.</p>
</div></section>
<section id="guides" class="alt"><div class="wrap">
<p class="kicker">Guides &amp; templates</p><h2>Practical guides</h2>
<div class="cards">{prods}</div>
</div></section>
</main>
<footer><div class="wrap">
<p><strong>Plainfold</strong>: a tiny studio making guides, templates &amp; small tools.</p>
<p class="links"><a href="{B["apifyProfile"]}">Apify</a><a href="{B["github"]}">GitHub</a><a href="https://plainfold.gumroad.com">Gumroad</a><a href="{B["x"]}">X</a><a href="/llms.txt">llms.txt</a></p>
</div></footer>
</body>
</html>
'''


def llms_txt():
    L = [f'# {B["name"]}', "", f'> {B["tagline"]} Plainfold publishes pay-per-result data tools that AI agents can call as remote MCP servers '
         "(hosted by Apify), plus practical guides.", "",
         f"All tools in one MCP server (streamable HTTP): {ALL_URL}",
         "Auth: OAuth sign-in with a free Apify account, or the header `Authorization: Bearer <APIFY_TOKEN>`. Agents without an account can pay per use with x402 or Skyfire through Apify.", "",
         "## Tools", ""]
    for t in TOOLS:
        L.append(f'- [{t["name"]}]({apify_url(t)}.md): {t["summary"]} Price: {t["priceShort"]}. MCP: {mcp_url([t["slug"]])} (tool `{tool_name(t)}`)')
    L += ["", "## Docs", "",
          f'- [Setup for MCP clients]({B["repo"]}/blob/main/README.md): Claude, Claude Code, Cursor, VS Code and generic MCP config, plus example calls',
          f'- [Full details for LLMs]({B["site"]}/llms-full.txt): every tool\'s inputs, outputs, use cases and prices on one page',
          "", "## Guides", ""]
    for p in PRODUCTS:
        L.append(f'- [{p["name"]}]({p["url"]}): {p["summary"]} Price: ${p["price"]}.')
    L += ["", "## Optional", "",
          f'- [MCP Registry entries](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.plainfold): io.github.plainfold/*',
          f'- [Apify profile]({B["apifyProfile"]})', f'- [GitHub]({B["github"]})', ""]
    return "\n".join(L)


def llms_full():
    L = [f'# {B["name"]}: full tool reference', "", f'> {B["tagline"]}', "", f"Updated {TODAY}.", "",
         "## How to call these tools", "",
         f"- Remote MCP server (streamable HTTP), all tools: {ALL_URL}",
         "- One tool only: https://mcp.apify.com/?tools=plainfold/<tool-slug>",
         "- Auth: OAuth with an Apify account, or `Authorization: Bearer <APIFY_TOKEN>`. Runs are billed per event at the prices below.",
         "- Agents without an Apify account: Apify agentic payments (x402 USDC on Base, or Skyfire).",
         "- Plain HTTP: POST https://api.apify.com/v2/acts/plainfold~<tool-slug>/run-sync-get-dataset-items with the JSON input as the body.",
         "- The MCP tool for each Actor also accepts `waitSecs` (how long the call waits for results). Longer runs return a run ID; fetch results with get-actor-run / get-dataset-items.", ""]
    for t in TOOLS:
        L += [f'## {t["name"]}', "", t["summary"], ""]
        L += [f"- {d}" for d in t["does"]]
        L += ["", f'Use it for: {t["useFor"]}', f'Not for: {t["notFor"]}', f'Price: {t["price"]}', "",
              f'MCP URL: {mcp_url([t["slug"]])}', f'MCP tool name: {tool_name(t)}', f'Apify page: {apify_url(t)}',
              f'Full README (markdown): {apify_url(t)}.md', "", f'Example prompt: "{t["examplePrompt"]}"', "", "Example input:", "",
              "```json", json.dumps(t["exampleInput"], indent=2), "```", ""]
    for p in PRODUCTS:
        L += [f'## {p["name"]}', "", p["summary"], "", f'Price: ${p["price"]} (one-time). Buy: {p["url"]}', ""]
    return "\n".join(L)


ROBOTS = """# Plainfold welcomes search engines and AI crawlers.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: meta-externalagent
Allow: /

User-agent: CCBot
Allow: /

User-agent: DuckAssistBot
Allow: /

User-agent: MistralAI-User
Allow: /

User-agent: cohere-ai
Allow: /

Sitemap: https://plainfold.github.io/sitemap.xml
"""


def sitemap():
    urls = ["/", "/llms.txt", "/llms-full.txt"]
    body = "".join(f"<url><loc>{B['site']}{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def build_site(site):
    write(os.path.join(site, "index.html"), index_html())
    write(os.path.join(site, "llms.txt"), llms_txt())
    write(os.path.join(site, "llms-full.txt"), llms_full())
    write(os.path.join(site, "robots.txt"), ROBOTS)
    write(os.path.join(site, "sitemap.xml"), sitemap())
    write(os.path.join(site, ".nojekyll"), "")


if __name__ == "__main__":
    build_servers()
    readme()
    if len(sys.argv) > 1:
        build_site(sys.argv[1])
    print("built", [t["slug"] for t in TOOLS])
