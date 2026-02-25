# S7-C Thread Reflection

## What Worked

1. Fixing the root lifecycle issue centrally in `CaptureDatabase` removed warning risk across all runtime DB methods without changing external behavior.
2. Adding focused lifecycle tests made connection-close guarantees explicit and regression-resistant.
3. Running backend tests with `ResourceWarning` escalated to errors provided strong validation that warning noise is removed.

## What Was Tricky

1. sqlite context manager behavior is subtle: it manages transactions but does not close the connection.
2. Warning emission can be GC-timing-dependent in generic test runs, so strict warning-mode execution and explicit warning-capture tests were needed for reliable evidence.

## Risks / Residual Gaps

1. Future direct `sqlite3.connect(...)` usage outside `CaptureDatabase` can reintroduce warning noise if explicit close management is not followed.
2. This thread intentionally did not broaden into runtime architecture refactors; only warning-source paths were changed.

## Follow-Ups

1. Add a lightweight code-review checklist item for sqlite usage (`close`/`closing`/close-managed context required).
2. Keep running backend CI tests with `PYTHONWARNINGS=error::ResourceWarning` for early detection of new lifecycle regressions.
