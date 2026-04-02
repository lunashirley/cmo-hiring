# Challenge 04: Blog-to-Multiplatform Repurposing for Abugo Portfolio

> **Type**: Creative

## Context

The Abugo portfolio companies (Reservio, Smartsupp, Survio, etc.) publish blog content — technical articles, case studies, product updates. The problem: a blog post gets published once and forgotten, even though it contains material for 10+ pieces of platform-specific content across multiple channels.

## What Is Blog-to-Multiplatform Repurposing?

Instead of manually rewriting a blog post for each social channel, you build a **pipeline** that:
- Takes a **blog post URL** as input
- **Extracts** the key content atoms — stats, quotes, insights, stories, takeaways
- **Adapts** each atom into platform-native content for multiple channels (LinkedIn, Twitter/X, newsletter, Instagram, short-form video script, etc.)
- **Outputs** ready-to-publish content across all target platforms

A LinkedIn post should read like LinkedIn, a tweet like a tweet — not just the same text at different lengths. The pipeline is what we want to see — not hand-crafted social posts.

## Pick Your Focus

**Source blog** (pick 1 post from any of these):
- [Smartsupp blog](https://www.smartsupp.com/blog/)
- [Reservio blog](https://www.reservio.com/blog/)
- [Survio blog](https://www.survio.com/blog/)
- [Shopsys blog](https://www.shopsys.com/blog/)

**Target platforms** (pick at least 4):
- LinkedIn, Twitter/X, Newsletter, Instagram carousel, Short-form video script (Reels/TikTok/Shorts), Dev community (Dev.to, Hashnode), Podcast show notes

## Your Task

Build a pipeline that takes a single blog post and produces **multiplatform content across your chosen channels**.

1. **Pick a real blog post** from the sources above
2. **Build the pipeline** — prompts, scripts, agents, or automation that decompose the article and produce platform-native content for each channel
3. **Run it** — produce all platform outputs from one source article. Raw pipeline output is fine, don't hand-edit.

## Deliverables

Put your work into the `pipeline/` and `output/` folders:

- `pipeline/` — your prompts, scripts, agent configs, workflow exports, whatever powers the repurposing
- `output/` — the generated multiplatform content from your chosen blog post

## Example Output Shape

Your output might look something like this (format is up to you):

```
📝 Source: "How AI Chatbots Reduce Support Costs by 40%" (Smartsupp blog)

LINKEDIN POST 1 — Key insight angle
  "We analyzed 10,000 support conversations. Here's what we found..."
  [generated post, ~150 words]

LINKEDIN POST 2 — Contrarian take
  "Most companies add more support agents. The smart ones..."
  [generated post, ~100 words]

TWITTER/X THREAD (7 tweets)
  1/ "Your support team is answering the same 5 questions 80% of the time. Here's what to do about it 🧵"
  2/ "We looked at the data across 10k conversations..."
  ...

NEWSLETTER SECTION (~200 words)
  "This week's pick: the real numbers behind AI support..."
  [generated digest]

INSTAGRAM CAROUSEL (5 slides)
  Slide 1: "AI support isn't replacing your team" (hook)
  Slide 2: "40% cost reduction — here's how" (stat)
  Slide 3: "The top 5 questions bots handle best" (value)
  Slide 4: "Real example: before vs. after" (proof)
  Slide 5: "Try it free — link in bio" (CTA)
```

Don't stress the format — we want to see the pipeline producing platform-native content, not polished posts.

## Loom Video (required)

5-15 min walkthrough: your repurposing framework, a live demo with the blog post showing outputs across platforms, and briefly cover:
- How would you **schedule** the derived content across platforms? (timing, order, tools)
- How would you **measure** which platforms and formats perform best?
- How would you **trigger** this automatically when a new blog post is published?

## Time Budget

~2 hours. Build the pipeline, run it, record the Loom.

---

## How to Approach This

1. **Do your research** — pick a real blog post from our portfolio companies and study the content
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
