# Challenge 05: Competitive Intelligence for Smartsupp vs. Tidio

> **Type**: Analytical

## Context

[Smartsupp](https://smartsupp.com) is a live chat & AI chatbot platform for e-commerce (part of the Abugo portfolio). [Tidio](https://tidio.com) is a direct competitor targeting the same audience. Abugo's portfolio companies currently track competitors ad-hoc — someone spots a change, shares it in Slack, and it gets forgotten.

## What Is a Competitive Intelligence Engine?

Instead of occasional googling about competitors, you build a **system** that:
- **Collects** competitive signals from public sources (websites, pricing pages, G2/Capterra reviews, blog content, social media, job postings, changelogs)
- **Analyzes** the data — spots positioning shifts, pricing changes, feature gaps, content strategy differences
- **Produces** an actionable report with specific recommendations, not just "competitor X did Y"

The system and analytical methodology are what we want to see — not just a one-time competitive analysis.

## Pick Your Focus

**Portfolio company + competitor pair** (pick 1):
- **Reservio** vs. Calendly, Acuity, Fresha, Booksy, or SimplyBook.me
- **Smartsupp** vs. Tidio, Intercom, LiveChat, Drift, or Crisp
- **Survio** vs. Typeform, SurveyMonkey, Tally, or Google Forms
- **Tanganica** vs. AdRoll, Criteo, or Google Performance Max
- **Shopsys** vs. Shopify, commercetools, or BigCommerce

## Your Task

Build a competitive intelligence system for your chosen **portfolio company vs. competitor**.

1. **Research** both products using public data — websites, pricing, features, reviews, content, social media
2. **Build the system** — prompts, scripts, agents, or automation that collect and analyze competitive signals
3. **Run it** — produce a competitive intelligence report covering positioning, pricing, features, reviews, content strategy, and actionable recommendations

## Deliverables

Put your work into the `system/` and `output/` folders:

- `system/` — your prompts, scripts, agent configs, workflow exports, whatever powers the intelligence gathering
- `output/` — the competitive intelligence report for Smartsupp vs. Tidio

## Example Output Shape

Your report might look something like this (format is up to you):

```
🔍 Competitive Intelligence Report — Smartsupp vs. Tidio

POSITIONING
  Smartsupp: "Boost online sales with AI" — product-led, e-commerce focus
  Tidio: "Grow sales with AI customer service" — broader, service-first
  Gap: Tidio positions harder on "customer service", Smartsupp on "sales"
  → Recommendation: Smartsupp should own the "revenue from chat" angle more aggressively

PRICING
  Smartsupp: Free → €14 → €19.50 → custom
  Tidio: Free → €29 → €59 → €2999
  Gap: Tidio's jump from free to paid is steep (€29 vs €14)
  → Recommendation: Smartsupp's pricing is a competitive advantage — emphasize it in remarketing

FEATURES
  Tidio has: email marketing, advanced analytics, Shopify deep integration
  Smartsupp has: video recordings, unique visitor insights
  Gap: Tidio's Shopify integration is stronger
  → Recommendation: prioritize Shopify integration if targeting e-commerce segment

REVIEW SENTIMENT (G2/Capterra)
  Smartsupp: 4.6/5 — praised for ease of use, criticized for limited integrations
  Tidio: 4.7/5 — praised for chatbot builder, criticized for pricing jumps
  → Recommendation: leverage Tidio's pricing complaints in competitive positioning

CONTENT & SEO
  Tidio publishes 8-10 blog posts/month, ranking for "live chat for..."
  Smartsupp publishes 2-3/month
  → Recommendation: increase content velocity on comparison + alternative keywords
```

Don't stress the format — we want to see the system producing actionable insights, not a polished report.

## Loom Video (required)

5-15 min walkthrough: your intelligence framework, a live demo of the system, and briefly cover:
- How would you **distribute** these insights to stakeholders? (format, cadence, channels)
- How would you **prioritize** which insights need immediate action vs. long-term tracking?
- How would you **automate** ongoing monitoring so this runs weekly without manual effort?

## Time Budget

~2 hours. Build the system, run it, record the Loom.

---

## How to Approach This

1. **Do your research** — use publicly available data about Smartsupp and Tidio (websites, reviews, pricing, content, social media)
2. **Build a pipeline** — connect inputs to outputs using whatever tools you think are useful
3. **Create skills, agents, or rules** — show us reusable building blocks and the thinking behind them. No constraints, full creative freedom.
4. **Don't overthink the automation** — it doesn't need to be perfect or super technical. Once you're hired, you'll refine it with our automation team. We want to see your approach, not production-ready code.

## Tools

Use whatever gets the job done. We're especially interested in **AI-native workflows** — Claude Code, Claude Cowork, Cursor, custom skills/agents/rules.

## What We're Looking For

- **Process over polish** — show us a working system, not hand-crafted outputs
- **AI fluency** — build repeatable workflows, not one-off text generation
- **Strategic depth** — real marketing logic behind the automation
- **The Loom video matters most** — we want to hear how you think
