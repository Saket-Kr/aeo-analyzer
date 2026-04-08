# Prompt Iteration Log

## Draft 1: Structured Prompt with Type Definitions

```
You are a search query decomposition engine that simulates how AI-powered
search engines break down user queries into sub-queries for comprehensive
answer generation.

Given a target query, generate 10 to 15 sub-queries distributed across
these 6 types:

1. comparative — Compare the subject against alternatives or competitors
2. feature_specific — Focus on a specific capability, feature, or attribute
3. use_case — Real-world application or scenario where the subject is applied
4. how_to — Step-by-step procedural or instructional query
5. trust_signals — Reviews, case studies, credibility markers, social proof
6. definitional — Conceptual "what is" query explaining the subject

Generate at least 2 sub-queries per type. Return a JSON object with key
"sub_queries" containing an array of objects with "type" and "query" fields.
```

**Input:** `best AI writing tool for SEO`

**Output:**
````
```json
{
  "sub_queries": [
    {"type": "comparative", "query": "Compare the top AI writing tools for SEO: Jarvis, Surfer SEO, and Copy.ai"},
    {"type": "comparative", "query": "Which is better for SEO content: Jasper or Anyword?"},
    {"type": "feature_specific", "query": "What AI writing tools offer keyword optimization features for SEO?"},
    {"type": "feature_specific", "query": "Do any AI writing tools integrate with Google Analytics for SEO tracking?"},
    {"type": "use_case", "query": "How can AI writing tools help in creating blog posts that rank higher on Google?"},
    {"type": "use_case", "query": "Using AI tools to generate SEO-optimized product descriptions"},
    {"type": "how_to", "query": "How to use AI writing tools to improve on-page SEO"},
    {"type": "how_to", "query": "How to configure an AI writing assistant for SEO content creation"},
    {"type": "trust_signals", "query": "Best AI SEO writing tools with verified user reviews and case studies"},
    {"type": "trust_signals", "query": "Are there case studies showing AI writing tools improving SEO rankings?"},
    {"type": "definitional", "query": "What is an AI writing tool and how does it assist with SEO?"},
    {"type": "definitional", "query": "Define AI-powered SEO writing and its benefits"}
  ]
}
```
````

**What worked:**
- Correct JSON structure — flat array, correct field names.
- All 6 types present, 2 each. The type descriptions helped.

**Problems found:**
- **Markdown code fences.** The model wrapped output in `` ```json ... ``` ``, which breaks `json.loads()` directly. I had to add string stripping logic to handle this, which felt brittle.
- **Type bleed between `use_case` and `how_to`.** The `use_case` entry "How can AI writing tools help in creating blog posts..." reads like a `how_to`. The descriptions weren't differentiated enough.
- **Sub-queries were generic.** "Compare the top AI writing tools" and "What AI writing tools offer keyword optimization" are things anyone could write without an LLM. They don't feel like what an actual search engine decomposition would produce — too surface-level, not enough specificity.
- **No diversity constraint.** Running it multiple times gave near-identical outputs. The model was templating rather than generating.

---

## Draft 2 (Final): Example-Driven + Diversity + Specificity

Key changes from Draft 1:
- Added a **complete JSON example** using a different query topic ("best CRM software for startups") so the model sees the expected style without copying.
- Added **explicit rules**: diversity ("avoid near-duplicates"), specificity ("must be specific to the provided target query"), and type exclusivity ("only use the 6 types listed above").
- Expanded **type descriptions** to reduce overlap — "real-world application or scenario" (use_case) vs "step-by-step procedural or instructional" (how_to).
- Grounded the role in **real systems** — "Perplexity, ChatGPT Search, Google AI Mode" — to prime the model for realistic decomposition patterns.

```
You are a search query decomposition engine. Given a target query, you
simulate how AI-powered search engines (Perplexity, ChatGPT Search,
Google AI Mode) decompose it into sub-queries to build a comprehensive
answer.

Generate 10 to 15 sub-queries across these 6 types. Produce at least
2 sub-queries for each type.

Sub-query types:
1. comparative — Compare the subject against alternatives or competitors
2. feature_specific — Focus on a specific capability, feature, or attribute
3. use_case — Real-world application or scenario where the subject is applied
4. how_to — Step-by-step procedural or instructional query
5. trust_signals — Reviews, case studies, credibility markers, social proof
6. definitional — Conceptual "what is" query explaining the subject

Rules:
- Each sub-query must be specific to the provided target query
- Sub-queries must be diverse — avoid near-duplicates
- Only use the 6 types listed above
- Return a JSON object with a single key "sub_queries" containing an
  array of objects, each with "type" and "query" fields

Example for target query "best CRM software for startups":

{
  "sub_queries": [
    {"type": "comparative", "query": "HubSpot vs Salesforce vs Pipedrive for startups"},
    {"type": "comparative", "query": "free CRM vs paid CRM for early stage startups"},
    {"type": "feature_specific", "query": "CRM with automated lead scoring for small teams"},
    {"type": "feature_specific", "query": "CRM software with built-in email marketing integration"},
    {"type": "use_case", "query": "CRM for managing investor relations at a startup"},
    {"type": "use_case", "query": "using CRM to track product-led growth signups"},
    {"type": "how_to", "query": "how to migrate from spreadsheets to a CRM system"},
    {"type": "how_to", "query": "how to set up a sales pipeline in a CRM for B2B startup"},
    {"type": "trust_signals", "query": "CRM software reviews from YC-backed startup founders"},
    {"type": "trust_signals", "query": "case studies of startups scaling with CRM automation"},
    {"type": "definitional", "query": "what is a CRM and why do startups need one"},
    {"type": "definitional", "query": "CRM vs spreadsheet for customer management"}
  ]
}
```

**Input:** `best AI writing tool for SEO`

**Output (prompt-based, no guided decoding):**
```json
{
  "sub_queries": [
    {"type": "comparative", "query": "Jasper vs SurferSEO vs Frase for AI-powered SEO writing"},
    {"type": "comparative", "query": "AI writing tools for SEO vs traditional content agencies"},
    {"type": "feature_specific", "query": "AI writing tool with keyword density optimization"},
    {"type": "feature_specific", "query": "SEO-focused AI tool that supports content briefs and topic clusters"},
    {"type": "use_case", "query": "using AI to create SEO-optimized blog posts for affiliate marketing"},
    {"type": "use_case", "query": "AI writing tool for optimizing product descriptions for e-commerce SEO"},
    {"type": "how_to", "query": "how to use AI tools to write meta titles and descriptions for SEO"},
    {"type": "how_to", "query": "how to structure SEO content using an AI writing assistant"},
    {"type": "trust_signals", "query": "best AI SEO writing tools reviewed by digital marketing agencies"},
    {"type": "trust_signals", "query": "case studies showing improved search rankings using AI content tools"},
    {"type": "definitional", "query": "what is an AI writing tool and how does it help with SEO"},
    {"type": "definitional", "query": "difference between AI writing tools and traditional SEO content strategies"}
  ]
}
```

**Improvements over Draft 1:**
- **No markdown wrapping.** The in-prompt example (shown without fences) trained the model to respond with raw JSON.
- **Clean type separation.** No more `use_case`/`how_to` bleed. "using AI to create SEO-optimized blog posts for affiliate marketing" is clearly a use case; "how to structure SEO content using an AI writing assistant" is clearly procedural.
- **Specific, non-generic queries.** "AI writing tool with keyword density optimization" and "content briefs and topic clusters" show real domain awareness, not just rephrased versions of the input query.
- **Different-topic example worked.** The CRM example forced generalization — the model didn't copy "HubSpot vs Salesforce" into the SEO context.

---

## Prompt-Based vs Guided Decoding

With Draft 2 finalized, I tested two delivery strategies:

### Prompt-Based (PromptBasedStrategy)

Append "Return ONLY the JSON object. No markdown, no code blocks, no explanation." to the system message. Parse `response.choices[0].message.content` directly.

**Result:** Worked with Qwen3-235B. Valid JSON, no fences, correct structure.

**Risk:** With smaller models (8B, 20B on the same vLLM server), this remains unreliable — they frequently wrap output in markdown or add prose.

### Guided Decoding (GuidedDecodingStrategy)

Pass a JSON schema via `response_format` parameter. vLLM's guided decoding constrains token generation at the inference level to only produce JSON matching the schema.

**Output (guided decoding, same prompt):**
```json
{
  "sub_queries": [
    {"type": "comparative", "query": "Jasper vs SurferSEO vs Frase for AI-powered SEO writing"},
    {"type": "comparative", "query": "AI writing tools for SEO vs traditional content agencies"},
    {"type": "feature_specific", "query": "AI tool with keyword density optimization for SEO"},
    {"type": "feature_specific", "query": "AI writing tool that integrates with Google Search Console"},
    {"type": "use_case", "query": "generating meta descriptions using AI for higher CTR"},
    {"type": "use_case", "query": "creating blog outlines with AI based on SERP analysis"},
    {"type": "how_to", "query": "how to optimize content with AI tools for featured snippets"},
    {"type": "how_to", "query": "how to use AI writing tools for local SEO content creation"},
    {"type": "trust_signals", "query": "SEO agency reviews of AI content writing software"},
    {"type": "trust_signals", "query": "case studies showing improved rankings with AI writing tools"},
    {"type": "definitional", "query": "what is an AI writing tool and how does it help SEO"},
    {"type": "definitional", "query": "AI writing tool vs SEO content analyzer software"}
  ]
}
```

**Comparison:**

| Concern | Prompt-based | Guided decoding |
|---------|--------------|-----------------|
| Invalid JSON | Possible (needs retry) | Impossible |
| Extra/wrong fields | Possible | Impossible (`additionalProperties: false`) |
| Invalid type values | Possible | Impossible (enum constraint on type field) |
| Markdown wrapping | Depends on model | Cannot happen |
| Sub-query quality | Same | Same |

Both strategies produce equivalent content quality — guided decoding doesn't change what the model *wants* to say, only guarantees the structure it says it in. The prompt still drives quality; the schema drives validity.

**Decision:** `GuidedDecodingStrategy` as the default. `PromptBasedStrategy` kept as a fallback for providers without guided decoding support.

---

## Temperature Tuning

Tested Draft 2 with guided decoding at 0.3, 0.5, 0.7, and 1.0:

- **0.3:** Formulaic. Multiple runs produced nearly identical sub-queries.
- **0.5:** Reasonable variety but templated patterns repeated across runs.
- **0.7:** Good balance. Different runs produce meaningfully different sub-queries while staying relevant and well-typed.
- **1.0:** Occasional odd queries that stretch the type definition or lose relevance to the target query.

**Decision:** 0.7 as the default.
