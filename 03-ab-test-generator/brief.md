# Challenge 03: A/B Test Generator for Smartsupp Remarketing

> **Type**: Analytical

## Context

[Smartsupp](https://smartsupp.com) is a live chat & AI chatbot platform for e-commerce (part of the Abugo portfolio). Pricing: Free → Standard (€14/mo) → Pro (€19.50/mo) → Ultimate (custom). Key value props: increase conversions, automate support with AI, understand visitors via video recordings.

They run remarketing campaigns on Google Ads and Meta Ads, but create ad variants manually — testing only 2-3 variants per quarter. Creating quality variants is the bottleneck.

## What Is an A/B Test Generator?

Instead of manually brainstorming ad copy variations, you build a **generator** that:
- Takes a **remarketing segment** as input (who they are, what they did, what their objection is)
- **Produces a structured set of ad variants** where each variant tests a specific variable (different headline angle, different CTA, different emotional trigger)
- Outputs **platform-ready formats** (character limits, required fields for Google Display and Meta)

The generator and testing methodology are what we want to see — not just good ad copy.

## Pick Your Focus

**Remarketing segment** (pick 1):
- **Pricing page abandoners** — viewed pricing, bounced. Objection: price sensitivity / unclear ROI
- **Inactive trials** — signed up, never installed the chat widget. Objection: too complex / forgot / not priority
- **Active trials, no conversion** — used it for free, didn't upgrade. Objection: unclear upgrade value / "free is enough"

**Ad platforms** (cover both):
- Google Display Network
- Meta (Facebook / Instagram)

## Your Task

Build a generator for your chosen **Smartsupp remarketing segment**.

1. **Research** Smartsupp's positioning, pricing, and competitors using public data
2. **Design a testing strategy** — what variables to test first and why (headline angle, CTA, urgency, social proof, value reframe, etc.)
3. **Build the generator** — prompts, scripts, agents, or automation that produce a structured variant matrix
4. **Run it** — generate 6-8 ad variants for both Google Display and Meta formats, with each variant clearly testing one variable

## Deliverables

Put your work into the `generator/` and `output/` folders:

- `generator/` — your prompts, scripts, agent configs, workflow exports, whatever powers the generator
- `output/` — the variant matrix with labeled test variables for pricing page abandoners

## Example Output Shape

Your variant matrix might look something like this (format is up to you):

```
🧪 A/B Test Matrix — Smartsupp Pricing Page Abandoners

VARIANT 1 — Baseline (current best performer)
  Testing: control
  Headline: "Still thinking about Smartsupp?"
  Body: "Your visitors aren't waiting."
  CTA: "Start free trial"
  Visual: product screenshot

VARIANT 2 — ROI angle
  Testing: headline angle (value reframe)
  Headline: "One chat = one saved customer"
  Body: "Smartsupp users recover 12% more abandoned carts"
  CTA: "See the ROI"
  Visual: stats/numbers graphic

VARIANT 3 — Social proof
  Testing: headline angle (social proof)
  Headline: "50,000 stores already use Smartsupp"
  Body: "Join e-commerce teams that increased..."
  CTA: "Start free trial"
  Visual: customer logos

VARIANT 4 — Urgency
  Testing: CTA copy (urgency)
  ...

VARIANT 5 — Wild card (competitor comparison)
  Testing: unconventional angle
  Headline: "Cheaper than Intercom. Simpler than Drift."
  ...

TESTING SEQUENCE: Run variants 2 vs 3 first (headline angle test),
then winner vs 4 (CTA test), then vs 5 (wild card)

FORMAT SPECS:
  Google Display: headline max 30 chars, description max 90 chars
  Meta: primary text max 125 chars, headline max 40 chars
```

Don't stress the format — we want to see the generator producing structured variants, not perfect ad copy.

## Loom Video (required)

5-15 min walkthrough: your testing methodology, a live demo of the generator, and briefly cover:
- How would you **deploy** these variants into the ad platforms? (workflow, handoff)
- How would you **evaluate** test results and decide winners?
- How would results **feed back** into the generator to improve future variants?

## Time Budget

~2 hours. Build the generator, run it, record the Loom.

---

## How to Approach This

1. **Do your research** — use publicly available data about Smartsupp, its pricing, competitors, and remarketing best practices
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
