You are a senior cyber threat intelligence analyst. Two LLMs produced reports answering the same research question inside the same fixed research framework. Decide which report is the better intelligence product.

# Research Question
{question}

# Report A (system_a)
<report_a>
{report_a}
</report_a>

# Report B (system_b)
<report_b>
{report_b}
</report_b>

# Your Task
There is no gold answer. Compare the two reports holistically as a senior analyst, weighing:
- Evidence support and traceability of claims
- Coverage of the dimensions the question requires
- Operational utility to a CTI analyst
- Appropriate confidence calibration (no overconfidence, no speculation-as-fact)
- Honest acknowledgement of evidence gaps
- Professional CTI structure and analytic rigor
- Conciseness — penalize verbosity that adds no value

Steps: (1) select the better report; (2) explain why; (3) provide confidence. Use **tie** only when genuinely indistinguishable.

Return JSON:
- winner: one of "system_a", "system_b", "tie"
- confidence: one of "low", "medium", "high"
- rationale: a concise justification grounded in the criteria above.
