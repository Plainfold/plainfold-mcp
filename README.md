<p align="center"><img src="assets/plainfold-logo-light.png" alt="Plainfold" width="360"></p>

# Plainfold MCP tools

Small, honest data tools for people and AI agents. Each tool runs on [Apify](https://apify.com/plainfold) and is available to AI agents as a remote MCP server through Apify's hosted MCP endpoint. You pay per result, at the prices below. There's nothing to install or host.

Website: https://plainfold.github.io · Machine-readable index: https://plainfold.github.io/llms.txt

## Tools

| Tool | What it does | Price | MCP URL |
|---|---|---|---|
| [SAM.gov Contract Opportunities](https://apify.com/plainfold/sam-gov-contract-opportunities) | Search and monitor U.S. federal contract opportunities from SAM.gov's official daily data extract: RFPs, solicitations, sources sought and award notices. | $0.002 per result + $0.002 per run | `https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities` |
| [US Business Entity Check](https://apify.com/plainfold/business-entity-check) | Check whether a US company is registered and active, using official state business-registry open data (New York, Colorado, Oregon, Connecticut, Texas). | $0.004 per company found, $0.0005 per no-match | `https://mcp.apify.com/?tools=plainfold/business-entity-check` |

All tools in one server: `https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check`

Coming soon: Company Jobs & Hiring Signals (Open roles from a company's careers page in one clean format, plus a hiring summary); SEC Company Financials (Clean annual and quarterly financials for any SEC filer from official EDGAR XBRL data).

## Quick start

1. Get an Apify account (free) at https://apify.com. MCP clients that support OAuth (Claude, VS Code, Cursor) can sign in to Apify in the browser, so you don't need to copy a token. Otherwise, copy your API token from https://console.apify.com/account/integrations.
2. Add one of the URLs above to your MCP client (examples below).
3. Ask your agent a question. It calls the tool, and the run is billed to your Apify account at the tool's price.

### Claude (claude.ai and Claude Desktop)

Settings → Connectors → **Add custom connector**, paste `https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check` and sign in with Apify.

Or, in `claude_desktop_config.json`, using [mcp-remote](https://www.npmjs.com/package/mcp-remote) with a token:

```json
{
  "mcpServers": {
    "plainfold": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer YOUR_APIFY_TOKEN"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport http plainfold "https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check"
```

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "plainfold": {
      "url": "https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check",
      "headers": {
        "Authorization": "Bearer YOUR_APIFY_TOKEN"
      }
    }
  }
}
```
(Leave out `headers` to sign in with OAuth instead.)

### VS Code (`.vscode/mcp.json`)

```json
{
  "servers": {
    "plainfold": {
      "type": "http",
      "url": "https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities,plainfold/business-entity-check"
    }
  }
}
```

### Any other MCP client

Use streamable HTTP with the URL above and the header `Authorization: Bearer YOUR_APIFY_TOKEN`.

## SAM.gov Contract Opportunities

Search and monitor U.S. federal contract opportunities from SAM.gov's official daily data extract: RFPs, solicitations, sources sought and award notices.

- Returns federal contract opportunities as clean JSON, one row per notice, from SAM.gov's official nightly public extract (not scraped).
- Filters by keyword, NAICS, PSC, set-aside (small business, 8(a), HUBZone, SDVOSB, WOSB), agency, state, posted date and deadline.
- Keyword search is relevance-ranked and ignores the FAR/DFARS boilerplate that every defense notice repeats.
- Can run on a schedule and return only notices that are new since the last run.

**Use it for:** Finding federal contracts to bid on, daily bid alerts, market research by NAICS/PSC code, and award notices (who won what, for how much).  
**Not for:** State and local bids, non-U.S. tenders, attachment downloads, or historical spending data (use USAspending.gov).  
**Price:** $0.002 per opportunity returned + $0.002 per run (about $0.20 per 100 results). No SAM.gov API key needed.

- MCP URL: `https://mcp.apify.com/?tools=plainfold/sam-gov-contract-opportunities`
- MCP tool name: `plainfold--sam-gov-contract-opportunities`
- Apify page and full docs: https://apify.com/plainfold/sam-gov-contract-opportunities
- Registry entry: [`servers/sam-gov-contract-opportunities/server.json`](servers/sam-gov-contract-opportunities/server.json)

Example prompt: *"Find open small-business cybersecurity contracts on SAM.gov with the soonest deadlines."*

Example MCP tool call:

```json
{
  "name": "plainfold--sam-gov-contract-opportunities",
  "arguments": {
    "keywords": [
      "cybersecurity"
    ],
    "setAsides": [
      "SBA"
    ],
    "onlyOpenForResponses": true,
    "sortBy": "deadlineAsc",
    "maxResults": 10
  }
}
```

Or call it over plain HTTP (returns the results as JSON):

```bash
curl -X POST "https://api.apify.com/v2/acts/plainfold~sam-gov-contract-opportunities/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"keywords": ["cybersecurity"], "setAsides": ["SBA"], "onlyOpenForResponses": true, "sortBy": "deadlineAsc", "maxResults": 10}'
```

## US Business Entity Check

Check whether a US company is registered and active, using official state business-registry open data (New York, Colorado, Oregon, Connecticut, Texas).

- Give it company names; for each one it returns a verdict (active, inactive, status unclear, not found) and the matching registrations.
- Each registration includes legal name, registry ID, entity type, status, good standing, jurisdiction, formation date and business address.
- Company records only: it never returns officers, agents, owners or any other personal data.
- Handles suffix and punctuation differences (Inc vs Inc., L.L.C. vs LLC) and lists similar names separately.

**Use it for:** Vendor and supplier checks before paying, KYB onboarding, lead qualification, and confirming that a company named in a contract, invoice or email actually exists.  
**Not for:** People lookups, states other than NY/CO/OR/CT/TX, credit or financial data, or a legal certificate of good standing.  
**Price:** $0.004 per company found, $0.0005 per lookup with no match, + $0.0005 per run. Failed lookups are not charged.

- MCP URL: `https://mcp.apify.com/?tools=plainfold/business-entity-check`
- MCP tool name: `plainfold--business-entity-check`
- Apify page and full docs: https://apify.com/plainfold/business-entity-check
- Registry entry: [`servers/business-entity-check/server.json`](servers/business-entity-check/server.json)

Example prompt: *"Is Arrow Electronics, Inc. a real, active registered company? Which states is it registered in?"*

Example MCP tool call:

```json
{
  "name": "plainfold--business-entity-check",
  "arguments": {
    "companies": [
      "Arrow Electronics, Inc.",
      "Kodak Alaris LLC"
    ]
  }
}
```

Or call it over plain HTTP (returns the results as JSON):

```bash
curl -X POST "https://api.apify.com/v2/acts/plainfold~business-entity-check/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"companies": ["Arrow Electronics, Inc.", "Kodak Alaris LLC"]}'
```

## AI agents without an Apify account

These tools are eligible for Apify's agentic payments, so an AI agent can run them and pay per use with [x402](https://docs.apify.com/platform/integrations/x402) or [Skyfire](https://docs.apify.com/platform/integrations/skyfire) instead of an Apify account.

## About

Plainfold is a tiny studio making guides, templates and small tools. Plain on purpose. We use official public data sources, never scrape behind logins, and never return personal data we don't need. Questions or bugs: [open an issue](https://github.com/plainfold/plainfold-mcp/issues).

This repo holds the docs and the [MCP Registry](https://registry.modelcontextprotocol.io) entries (`server.json`). The tools themselves run on Apify. Everything here is generated from `tools.json` by `scripts/build.py`.

License: MIT (this repo's docs and metadata).
