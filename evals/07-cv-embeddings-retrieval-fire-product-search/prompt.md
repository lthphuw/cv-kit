---
description: Image similarity search with a CV encoder goes to cv-embeddings-retrieval.
expected_outcome: cv-embeddings-retrieval fires.
tags: [trigger, fire]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

I need image similarity search over about 2 million product photos. The plan is SigLIP2 embeddings in a FAISS index. How should I compute and normalise the embeddings so cosine search works?
