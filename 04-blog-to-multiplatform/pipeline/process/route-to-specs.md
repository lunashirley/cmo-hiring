# Route to Specs
*A working conversation on the Content Repurposing Pipeline.*

---

## LUNA

I am building a content repurposing pipeline as a Proof of Concept.

The goal is to take a single blog URL and atomize it into platform-native content for LinkedIn, Twitter (or as it is now known X), a Newsletter, and an Instagram Carousel.

I want you to help me plan its development first before building anything. Think long-term in a way that some elements may be repurposed & reused down the line.

My expectation is for us to discuss the specifications first, and help me capture possible shortcomings that I may have not considered I will be satisfied, I will want you to output planned specifications into .md file with a set of complete instructions.

**System Architecture (Planning Mode):**

**The Extractor:** First, use Jina Reader (https://r.jina.ai/[URL] or similar) to fetch the blog content, while offering alternative such as a simple copy/paste environment. Analyze the text to identify 'Content Atoms': key stats, unique insights, and punchy quotes.

**The Human-in-the-Loop Checkpoint:** Present these 'Atoms' to me for validation before generating any social copy for content repurposing.

**The Multi-Platform Agent Specialists:** Use a specialized agents to adapt these atoms into 4 distinct native formats (LinkedIn, Twitter/X, Newsletter, Instagram), while one more agent should act as Head of Content assessing the quality of the content. If it won't pass the quality check, return the output to individual agent to rework it.

**Self-learning mechanism:** Add an option for the human operator to mark which content was successful driving the results with a simple impact signalling (Worst, Low, Average, High, Best) to inform Head of Content Agent which content performs, and which doesn't.

**Templates:** Utilize specific pre-defined templates for native formats to ensure the output always adheres to platform-specific conditions and limitations.

**Brand voice:** Add an editable environment to define brand voice, which can be selected during the human in the loop checkpoint.

**Security:** Since this will be run on local host, do not bother with OAuth, perhaps include only a simple login.

**Logs:** Ensure that all operations are logged in a separate tab in the app especially actions of individual agents to validate their added value.

**Brain:** I want this to be able to run independently on localhost, consider using Ollama & qwen3-vl:30b model, which I have installed. But ensure this is a variable, not a constant in the platforms settings.

---

## CLAUDE

Before I commit anything to spec, here are the places where the architecture as drawn leaves meaningful decisions unmade, or contains failure modes I would rather design around than into.

**The QA loop has no floor.** If the Head of Content rejects output, what stops the rework? Local models will ping-pong. You need a max retry (two is typical), and on exhaustion either surface to human with annotations or pass with a quality flag. More importantly, "quality" is unfalsifiable without a rubric. The QA agent needs concrete criteria per platform: hook strength, CTA presence, length bands, atom fidelity, tone match, banned phrasings. Without that, its judgment is mood.

**"Self-learning" via a 5-point scale is storage, not learning.** For a PoC on local inference, the pragmatic mechanism is few-shot injection: feed top-rated past outputs as examples into each specialist's prompt on the next run. A single impact axis is also too coarse to learn from. Add why-it-worked tags at rating time (hook, length, CTA style, atom choice) or a short text field, otherwise you are training on noise.

**Atoms need a schema, not just a label.** I would propose typed objects: `{type: stat | insight | quote | anecdote, text, source_offset, proposed_angle, confidence}`. The HITL step then has real structure: approve, edit text, retype, add a manual atom, reorder by priority. Approve/reject alone wastes the human in the loop.

**Output editing before rating is the forgotten step.** If the operator can only rate what the agents produce, you lose the richest signal: their own edits. Let them tweak the output, save the diff, then rate. The diff becomes a learning artifact, the rating becomes meaningful.

**Instagram Carousel is the odd one out.** It is image-native. Decide now whether the agent produces slide copy plus layout guidance only, or whether the pipeline renders actual PNG slides (Playwright plus HTML templates is the clean path). The second doubles the complexity and materially changes the build. Either answer is fine; drifting between them mid-build is not.

**Brand voice deserves structure from day one.** A free-text field will drift into vagueness. Define a profile: tone descriptors, vocabulary do/don't, sentence-length preferences, reference examples, CTA patterns. Treat it as a selectable profile even if you start with one. What begins as a config field always becomes a table.

**qwen3-vl:30b is a vision-language hybrid.** For a pure text pipeline, a text-specialized model at the same parameter count usually writes better. Your "variable, not constant" principle is right; I would go further and bake in a model-per-agent override. QA might want a different model than the specialists. Atom extraction can run on something small and fast.

**Sequential execution will cost you minutes per article.** After HITL, the four specialists are independent. Fan them out in parallel, then run QA in parallel per output. Local inference latency is the single biggest UX tax, and parallelism is the cheap fix.

**Every stage must be restartable.** Fetch, extract atoms, approve atoms, generate, QA, present, rate. Persist each transition so you can resume from any point without redoing the one before. SQLite, typed tables, a clean `run_id` threaded through.

**Reusable modules to isolate from day one**, in line with your long-term lens:
- Content ingestion (Jina plus paste plus future connectors)
- Atom extractor (prompt plus schema)
- Agent orchestration pattern (specialists, QA, retry policy)
- Brand voice profile store
- Rating and few-shot feedback loop
- Template and prompt versioning
- Per-agent structured logging

Each should have a clean interface so it can be lifted into future tools without archaeology.

Before I draft the spec, five decisions I need from you:

1. **Instagram Carousel:** slide copy only, or rendered PNG slides?
2. **Tech stack:** FastAPI plus HTMX (lean), FastAPI plus React (familiar from Cortex), or other?
3. **Brand voice:** single, or multi-profile from day one? My recommendation is multi, even if you launch with one.
4. **Output editing in v1:** in scope or rating-only at first? My recommendation is in scope. The signal is too valuable to leave on the floor.
5. **Explicit out-of-scope list:** I would propose direct publishing, scheduling, image generation beyond IG slides, and multi-language. Confirm or adjust.

Once these are settled I will write the spec as a single `.md` with clean module boundaries, concrete rubrics, and stage-restartable orchestration.

> **Note** — I was pattern-matching your spec against the failure modes PoCs tend to collapse into once someone actually starts building. The nine critiques were not a complete list, they were the ones most likely to cause rework two weeks in: unbounded retry loops, ratings that do not actually train anything, flat atoms that waste the human checkpoint, and the Instagram ambiguity that quietly doubles build scope. The five questions at the end were ones I refused to answer for you. Each would have meaningfully changed the spec's shape, and picking them unilaterally would have meant writing a document you would then have to unpick.

---

## LUNA

Good points. Let's go one by one.

**1) QA Loop:** Let's go with 3 attempts as max. For HoC acting as QA agent, we will create those criteria in its own *.MD file, I think this may be the best for all agents involved, each should have their specific MD file.

**2) Self-learning:** 5 point system was proposed to indicate impact according to core metrics. Human operator may not know why it was actually successful. Propose simple system, that won't take human operator too much time, and will be user friendly with the above being considered.

**3) Atoms & Schema:** Makes sense, I like that. Consider UX for HITL (such as drag & drop during reprioritization, soft transitions, etc.)

**4) Output editing:** I like that step, it adds to learning parameters & can actually be considered alongside the actual content's impact. Consider simple storage though, and effective token utilization.

**5) Instagram Carousel:** We are just building copy, not image generation for this iteration. Prepare the structure for further usage of Playwright plus HTML templates, but do not plan for its implementation in this iteration just yet.

**6) Brand voice:** This will be defined in specific brand voice md file. These will be considered there, and should be respected by all content creating agents.

**7) Ollama model:** Fair, but let's not overengineer this just now. It should be mostly proof of concept. Let's leave per-agent model for late.

**8) Agent Execution:** Agreed, let's build the infrastructure to run agents in parallel if the hardware enables it and won't actually slow the process down or cause the process to terminate.

**9) Restartable stage:** Sure, no preference

**10) Reusable modules:** Makes sense, but Content ingestion & Atom extractor should be treated as one; Agent orchestration pattern & brand voice should be together; Learning such as rating, feedback loop, templating, versioning and logging should be one module too.

On the other specs / decisions you asked for:

1. Copy only
2. FastAPI + React
3. Multi-profile
4. Agreed, it's valuable input
5. No publication functions, but ensure the output is saved.

Now suggest if you have enough feedback, and if so create the md file I asked for initially.

---

## CLAUDE

Spec is ready. A few notes on choices I made where your feedback left room for interpretation:

**Rating system.** Kept your 5-point scale intact and layered a single optional multi-select ("hook, length, CTA, atom choice, tone, format, timing, other") on top. Zero required fields beyond the score. The edit diff does most of the attribution work quietly in the background, which is why I resisted adding a mandatory reason field.

**Edit storage.** Stored as unified diffs rather than full copies. Keeps the database lean and makes the "what did the operator change" signal explicit and machine-readable for the feedback loop.

**Feedback mechanism.** Few-shot exemplar injection rather than anything heavier. Top-5 rated outputs per platform/brand-voice pair form a rolling pool; top-3 seed the next generation. Edited versions outrank originals in the pool. Reversible, transparent, no training infrastructure.

**Instagram structure.** Interface for slide rendering is reserved in the data model and agent contract, but no Playwright code is written. When you are ready to add it later, the specialist already outputs per-slide copy in a shape that a renderer can consume.

**Section 14** flags four small decisions worth making at the start of the first build session rather than mid-flight. Worth glancing at before you or Claude Code begin.

One thing I would still raise: the spec assumes the login is a single static password. If you want even a gesture toward hygiene, an env-var-seeded password with a forced change on first run costs almost nothing. Happy to fold that in if you want it before you hand this off.

> **Note** — Your responses shifted three things meaningfully. First, the per-agent MD pattern you proposed for HoC was better than what I had in mind — so I extended it across every agent, which also solved the brand-voice-as-file requirement cleanly. Second, your "simple and user friendly" constraint on rating ruled out a reason field; that is why I landed on optional tags plus the edit diff as implicit signal, rather than asking for a written explanation. Third, your module regrouping was a clearer partition than mine — Module B keeping orchestration and brand voice together reflects that voice has no independent lifecycle from agent execution, which I had under-weighted. The login comment at the end was a raised hand, not a built-in addition. You explicitly scoped auth as "simple", so layering in more without asking would have been a small but real violation of your brief.
