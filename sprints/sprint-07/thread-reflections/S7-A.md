# S7-A Reflection (`AUT-15`)

## Summary
Implemented LLM-assisted tailored resume generation with deterministic fallback and strict source-backed claim mapping. Compliance and approval workflow behavior remained unchanged.

## What Worked
1. Layering LLM output on top of deterministic render-model generation reduced risk and kept fallback behavior straightforward.
2. Limiting LLM edits to bullet rewording with existing bullet IDs preserved claims-map traceability and compliance compatibility.
3. Extending generation tests for LLM success and provider-failure fallback gave direct regression protection for the new path.

## Friction
1. The generation path needed explicit claim evidence preservation so rewritten bullet text did not break source trace semantics.
2. Backend API test runs are log-heavy due structured observability output, which increases scan time during validation.

## Residual Risks
1. Real provider quality and response reliability are dependent on runtime provider implementation and prompt tuning.
2. Very large profile/job payloads may hit prompt truncation boundaries and reduce rewrite quality.

## Follow-Ups
1. Add provider-backed eval fixtures to score rewrite quality and factual consistency over representative job/profile corpora.
2. Consider exposing non-breaking generation metadata (mode/reason) in API responses for better runtime diagnosability.

## Commit
- `e61d339`
