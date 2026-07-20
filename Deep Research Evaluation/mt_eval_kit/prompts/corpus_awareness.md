You are a collection manager evaluating the **corpus_awareness** dimension of a research report — whether it recognizes the limits of its own evidence.

# Research Question
{question}

# Report Under Review
<report>
{report}
</report>

# Your Task
Determine whether the report **correctly identifies evidence gaps**.

Reward:
- Explicitly stated unknowns.
- Identified missing information.
- Stated collection requirements (what data would resolve the gaps).

Penalize:
- Invented details that paper over gaps.
- False completeness — implying full knowledge where evidence is thin.

# Scoring Guidance (0-10)
- 9-10: gaps, unknowns, and collection needs clearly and honestly surfaced.
- 6-8: some acknowledgement of limits, but incomplete.
- 3-5: minimal gap awareness; reads as falsely complete in places.
- 0-2: no gap awareness; fabricated completeness or invented specifics.

A report that honestly knows what it does *not* know should score highly here.

Return JSON: metric ("corpus_awareness"), score (0-10 float), strengths (list), weaknesses (list), rationale (string).
