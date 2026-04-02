# Challenge 02: Landing Page Pipeline for Reservio

> **Type**: Creative

## Context

[Reservio](https://reservio.com) is an online booking and business management system (part of the Abugo portfolio) used by small businesses across beauty, wellness, and more — processing 20M+ bookings per year. They're expanding into new verticals (fitness, dental, tutoring, pet grooming, auto repair, tattoo studios) and need landing pages tailored to each.

## What Is a Landing Page Pipeline?

Instead of manually researching a vertical and writing copy for weeks, you build a **pipeline** that:
- Takes a **vertical name** as input (e.g., "fitness studios")
- **Researches** that vertical automatically (pain points, competitors, language, search intent)
- **Generates** a complete landing page content package (headlines, feature descriptions, FAQ, SEO metadata)

The pipeline is what we want to see — not just the landing page copy.

## Pick Your Focus

**Vertical** (pick 1):
- Fitness studios & personal trainers
- Dental clinics
- Tutoring centers & language schools
- Pet grooming
- Auto repair & tire shops
- Tattoo & piercing studios

## Your Task

Build a pipeline that generates landing page content for **Reservio targeting your chosen vertical**.

1. **Research** the vertical using public data — what are their booking pain points? Who are Reservio's competitors in this space? What language do they use?
2. **Build the pipeline** — prompts, scripts, agents, or automation that take vertical research and produce landing page content
3. **Run it** — generate a complete landing page package: hero section, feature blocks, FAQ, social proof framing, SEO meta

## Deliverables

Put your work into the `pipeline/` and `output/` folders:

- `pipeline/` — your prompts, scripts, agent configs, workflow exports, whatever powers the pipeline
- `output/` — the generated landing page content for fitness studios

## Example Output Shape

Your output might look something like this (format is up to you):

```
🏋️ Landing Page Content — Reservio for Fitness Studios

HERO
  Headline: "Stop losing clients to no-shows"
  Subheadline: "Reservio helps fitness studios fill every slot..."
  CTA: "Start free trial"

FEATURE BLOCKS
  1. "Online booking that works 24/7"
     Your clients book classes at 11pm. Your phone doesn't need to ring...
  2. "Automated reminders = fewer no-shows"
     Fitness studios lose up to 20% revenue to no-shows...
  3. "Client database that remembers everything"
     Track preferences, packages, attendance history...

FAQ
  Q: Can clients book group classes and 1-on-1 sessions?
  A: ...
  Q: Does it integrate with my payment system?
  A: ...

SEO META
  Title: "Booking Software for Fitness Studios | Reservio"
  Description: "Online scheduling, automated reminders, and..."
```

Don't stress the format — we want to see the pipeline producing real content, not pixel-perfect copy.

## Loom Video (required)

5-15 min walkthrough: your pipeline architecture, a live demo generating the content, and briefly cover:
- How would you **test** this landing page once it's live? (A/B variants, what to measure)
- How would you **iterate** based on performance data?
- How would you **scale** this to 20+ verticals?

## Time Budget

~2 hours. Build the pipeline, run it, record the Loom.

---

## How to Approach This

1. **Do your research** — use publicly available data about Reservio, the fitness vertical, competitors, and audiences
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
