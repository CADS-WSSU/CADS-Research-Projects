You are a senior CTI analyst evaluating the **cti_quality** dimension — whether the report resembles a professional CTI product.

# Research Question
{question}

# Report Under Review
<report>
{report}
</report>

# Your Task
Judge whether the report reads like a polished, professional intelligence product in structure, presentation, and analytic rigor.

Consider the presence and quality of:
- Executive summary / BLUF
- Key findings
- Structured analysis
- ATT&CK mapping
- Indicators of compromise
- Campaign chronology
- Confidence language

# Scoring Guidance (0-10)
- 9-10: indistinguishable from a high-quality vendor/government product.
- 6-8: professional and well-structured with minor omissions.
- 3-5: recognizable as CTI but missing several expected elements.
- 0-2: unstructured, informal, or missing the hallmarks of an intelligence product.

Reward analytic rigor and standard CTI structure. Penalize disorganization and verbosity that obscures the product.

Return JSON: metric ("cti_quality"), score (0-10 float), strengths (list), weaknesses (list), rationale (string).
