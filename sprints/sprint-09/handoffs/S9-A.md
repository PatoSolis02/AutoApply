STATUS: DONE

branch: `codex/s9-a-auth-backend`
worktree: `/Users/pato/Library/CloudStorage/OneDrive-rit.edu/Desktop/worktrees/autoapply_s9_a_auth_backend`
commit hash: `PENDING`
issue: `AUT-34`

scope delivered:
1. Added backend auth primitives for signup/login/logout/session with new endpoints:
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/session`
2. Added deterministic auth/session error semantics with stable `error.code` values:
- `auth_required`
- `invalid_authorization_header`
- `invalid_credentials`
- `email_exists`
- `invalid_session`
- `session_expired`
3. Added deterministic session-expiry behavior:
- sessions include persisted `expires_at`
- expired session check occurs on session read/logout auth path
- expired sessions are revoked and return `401` with `session_expired`
4. Added auth persistence schema:
- `auth_users` table (unique email, password hash, timestamps)
- `auth_sessions` table (token hash, expiry/revocation/last-seen metadata)
5. Added backend contract tests for auth success/failure/expired-session paths in `backend/tests/test_auth_api.py`.
6. Updated architecture contract notes for auth endpoints and auth-specific `401` semantics in `docs/architecture/BUILD_CONTRACT.md`.

files changed:
- `backend/migrations/0003_auth_tables.sql`
- `backend/app/db.py`
- `backend/app/schemas.py`
- `backend/app/main.py`
- `backend/tests/test_auth_api.py`
- `docs/architecture/BUILD_CONTRACT.md`

tests/checks run:
1. `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- PASS (`Ran 73 tests`)

assumptions/risks:
1. Session TTL defaults to 12 hours via `AUTOAPPLY_AUTH_SESSION_TTL_SECONDS`; if unset/invalid, default remains 12h.
2. Existing non-auth backend endpoints remain ungated in this thread by design (AUT-36 covers broader per-user scoping/isolation).
3. Multiple concurrent sessions per user are currently allowed; global session invalidation semantics are not included in this scope.

contract notes:
1. Auth endpoints are additive and do not alter existing capture/tracking/generation endpoint paths.
2. Session tokens are opaque bearer tokens; only SHA-256 token hashes are persisted server-side.
3. Passwords are stored as PBKDF2-SHA256 hashes (`pbkdf2_sha256$iterations$salt$digest`), never plaintext.
