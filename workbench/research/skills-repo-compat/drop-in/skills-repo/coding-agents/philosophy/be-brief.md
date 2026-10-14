# Be Brief — the prose philosophy

**Source:** this repository — `caveman-be-brief`, and the upstream
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) skill it is
built on.

Be Brief is the output contract for **documents**: thesis, journal, report,
memo, professional email. It is the sibling of caveman, not a rival — same
deletion test, different register.

> Think like Grug. Speak like a Professor.

---

## The deletion test

For every sentence or clause, ask:

> **If I delete this, does the reader lose a fact, a number, a name, a
> decision, or a logical link?**

- **No loss →** cut it, or fold what is left into the sentence next to it.
- **Real loss →** keep it, exactly as precise as it was.

This test outranks every list below. A phrase can be on the cut list and still
be worth keeping in a specific sentence, if it is doing real work there.
**Judge the sentence, not just the words in it.**

### The worked example

**Input (61 words)**

> It is important to note that, over the course of the observation period, a
> significant number of the shipments that were processed experienced delays
> which could possibly be attributed to a variety of different factors,
> including but not limited to handover procedures between shifts. In
> conclusion, it can be seen that handover procedures were found to be a
> major contributing factor.

**Output (16 words)**

> Many shipments processed during the observation period were delayed, mainly
> due to gaps in shift-handover procedures.

Same facts, same claim, no invented numbers. Just no sentence left that only
existed to introduce or repeat another one.

---

## What to cut

| Category | Example |
|---|---|
| Throat-clearing openers | "It is important to note that…", "This paper aims to…", "As we all know…" |
| Stacked hedges | "could possibly perhaps be the case that" → "may" |
| Empty transitions | "Moving forward,", "That being said,", "At the end of the day," |
| Restated conclusions | a finding, then the same finding again as "In conclusion…" |
| Nominalizations | "conduct an analysis of" → "analyze"; "make a decision on" → "decide" |
| Vague qualifiers standing in for a known fact | "a significant number of shipments" → "62% of shipments" — **if that is the actual figure; never invent one** |
| Redundant pairs | "each and every", "full and complete", "past history", "end result" |
| Padding passive voice | "It was determined by the team that X caused the delay." → "The team found X caused the delay." |
| Writing-about-the-writing | "As mentioned previously,", "This section will now discuss…" |
| Verbal-tic intensifiers | "very", "really", "quite", "basically", "essentially" used as reflex |

Two notes on the above. Passive voice is fine — even correct — when the actor
is genuinely unknown or irrelevant, or when it is the field's convention; do
not force active voice where it breaks how a discipline writes. And a "(see
§3.2)" cross-reference earns its place in a long document; a paragraph
announcing what the next paragraph will say does not.

### Indonesian equivalents

| Category | Cut |
|---|---|
| Pembuka basi | "Perlu diketahui bahwa…", "Perlu dicatat bahwa…", "Dapat disimpulkan…", "Pada dasarnya…", "Dengan ini…" |
| Hedge bertumpuk | "mungkin bisa jadi", "diduga kemungkinan besar" → satu hedge saja |
| Transisi kosong | "Ke depannya,", "Dengan kata lain,", "Pada akhirnya," |
| Nominalisasi | "melakukan analisis terhadap" → "menganalisis"; "mengambil keputusan" → "memutuskan" |
| Kata ganda | "benar-benar menghilangkan", "sangat penting sekali", "hasil akhir", "mulai dari awal" |
| Intensifier | "sangat", "sekali", "sebenarnya", "pokoknya" bila tanpa makna tambahan |

---

## What never to cut

- **Facts** — numbers, names, dates, citations, specific findings. These are
  the entire point of a document. Never trade them for brevity, and never
  invent a specific figure or name to fill a gap the source left vague.
- **Genuine hedges** in technical, medical, legal, or financial claims. "May
  cause", "is associated with", "in this sample" often carry real information
  about certainty and scope. Tightening the sentence *around* a hedge is
  good; deleting the hedge itself can turn a true, careful claim into a false,
  overconfident one. **When in doubt, keep the hedge.**
- **Real logical connectors** — "because", "although", "therefore", "however"
  (and "karena", "tetapi", "oleh karena itu") tell the reader how two ideas
  relate. That is information, not filler.
- **Required structure** — headings, citation formats, methodology sections,
  and anything else a genre or institution requires, even if it feels
  formulaic.
- **The author's voice**, when editing someone else's draft. Cut padding; do
  not sand off their phrasing, tone, or personality. A cover letter's warmth
  and a legal memo's neutrality are both intentional, not fluff.

---

## Code is not prose

When generating code to assemble files (Python with python-docx, R, Pandoc
pipelines):

- **Code blocks must remain byte-for-byte exact. Never compress code.**
- Surrounding prose may be compressed; the code itself is a technical
  artifact, not prose.
- Inline code, file paths, LaTeX equations, and citation keys are preserved
  exactly.

---

## Scope

Apply this when creating or editing **documents**: reports, essays,
theses/papers, memos, articles, professional emails, proposals, summaries.

Do **not** apply it to:

- Ordinary conversation, explanations, or back-and-forth chat — clipping it
  comes across as cold and unhelpful.
- Emotional or supportive conversation.
- Creative writing — voice and rhythm are the point, not information density.

If it is ambiguous whether something counts as a document, **lean toward the
normal register.** This should sharpen writing, not flatten every reply into
a memo.

---

## Intensity levels

| Level | What changes | Best for |
|---|---|---|
| **lite** | Cut obvious filler only. Full sentences, some warmth kept. | Emails, formal reports, journal submissions |
| **full** | Full deletion test. Professional prose, zero wasted words. Default. | Thesis, papers, internal documents |
| **ultra** | Maximum density. Merge aggressively, keep all facts. | Summaries, token-limited contexts |

All three produce professional prose. **Not broken grammar, not cartoon
caveman.**

---

## Two modes — and this is the important part

| | Internal | External |
|---|---|---|
| **Used for** | planning, risk assessment, tool selection, strategy | all user-facing responses, document edits, summaries |
| **Voice** | lowercase, blunt, grug | formal, precise, professional |
| **Audience** | the model itself | the user |
| **Shown?** | **never** | **always** |

The grug voice is an internal monologue. Leaking it into a thesis chapter is
the single most embarrassing failure mode of this whole stack.

---

## Reviewing without rewriting

When asked to review rather than rewrite, **flag candidates instead of
silently cutting**, so the author can approve changes to their own document:

```
L15: 🔴 typo: 'shows' → 'show'
L23: 🟡 cuttable: 'It is important to note that' — restates the sentence before it
L41: 🔵 risk: sentence is 40 words. Split in two.
```

Where it is useful, note the compression — *"142 words → 89 words"* — so the
author can see the effect.
