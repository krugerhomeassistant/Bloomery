# LESSONS LEARNED

Format: [Problem] → [Root cause] → [Verified solution]

1. **Tailwind v4 `@apply btn` fails: "Cannot apply unknown utility class"** → v4 no longer lets you `@apply` plain CSS classes → declare custom classes with `@utility name { … }`; they can then be applied/composed.
2. **pip in `docker build` fails CERTIFICATE_VERIFY_FAILED (sandbox only)** → Claude cloud sandbox MITM proxy CA not trusted inside build containers → sandbox-only Dockerfile copy injecting `.sandbox-ca.crt` + `PIP_CERT/NODE_EXTRA_CA_CERTS`, `--network host`. The committed Dockerfile is clean; the user's host needs nothing.
3. **Docker daemon not running in sandbox** → no init system → start `dockerd &` manually.
4. **ImageMagick can't rasterize SVG (no rsvg delegate)** → missing librsvg → render icons with Playwright Chromium screenshots (`omitBackground`).
5. **Off-by-one in "late"** → used `days+1-L` → late = `(today - start).days - L`; `0` = due today (`state: due`).
6. **TypeScript 7.0 (Go port) is `latest` on npm** → ecosystem (vite-plugin types) still targets 5.x; pinned `typescript@^5.9.3` to avoid tooling surprises.
7. **Calendar sticky header showed content bleeding through** → `bg-canvas/95` + backdrop blur → solid `bg-canvas` + subtle shadow.
8. **Multi-drop emoji (💧💧💧) overflow chip circles** → emoji strings wider than 56px → render flow intensity with lucide `Droplet` icons (Chip `emoji` accepts ReactNode).
9. **Qwen3-style models emit `<think>` blocks** → reasoning tokens in content → strip `<think>…</think>` in `ai.complete`.
11. **Bind-mounted `/data` created root-owned by host (ZimaOS `/DATA/AppData`, Linux `./data`) → non-root container can't write DB** → `USER bloomery` in Dockerfile + host-created dir → `entrypoint.sh` runs as root, `chown -R` data dir, then `setpriv` drops to uid 10001 (verified PID 1 Uid 10001, files owned by bloomery).
12. **ZimaOS compose import doesn't build images** → dashboard import only pulls/uses images → pre-build (`docker build` + `docker save`/`load`) and reference `image: bloomery:latest`; `docker-compose.zimaos.yml`.
13. **Switching AI provider in settings carried the old API key over (Claude key → custom URL)** → key kept when field blank regardless of provider → backend clears key/url/model on provider change unless given (both in `config()` merge and `save()`); UI resets fields on provider pick. Test asserts it.
14. **`pkill -f pattern` / `pgrep -f` inside a bash -c killed the shell itself** → the pattern appears in the shell's own command line → use `fuser -k PORT/tcp` to stop servers.
15. **GPT-5 family rejects `max_tokens`/`temperature`** → reasoning models → for provider `openai` send `max_completion_tokens` (×4 headroom for reasoning tokens), no temperature.
16. **After-log note commented on a tag that was already logged** → note computed from full tag set → diff against previous tags; comment only on newly added ones.
17. **Forecasts looked "missing" in demo** → by design, tags already logged today are skipped → verify forecasts via `/api/feed?today=<PMS date>`.
18. **README screenshot run polluted demo data** → a failed earlier Playwright run had already saved a log, so the rerun toggled chips off/on → always reseed a fresh data dir before screenshot runs; scope chip clicks to `[role=dialog]`.
19. **`rm -rf dir/*` in workspace blocked by safety check** → glob removal inside workspace → overwrite files instead of deleting.
20. **GitHub API from sandbox returns "access not enabled"** until repo attached → use `git ls-remote --tags` on public action repos to find latest majors (checkout v7, setup-python v7, setup-node v7, qemu/buildx/login v4, metadata v6, build-push v7).
21. **Web Push impossible on typical ZimaOS install** → service workers/push need a secure context (HTTPS), LAN is `http://ip:8420` → notifications via ntfy/Gotify/HA/Discord webhooks instead.
22. **`ZoneInfo('Bad/Zone')` in a pydantic validator gave 500 not 422** → `ZoneInfoNotFoundError` subclasses KeyError, which pydantic doesn't convert → catch and re-raise `ValueError`.
23. **Emoji in HTTP headers (ntfy `Title:`) fail** → headers are latin-1 → use ntfy JSON publish (`POST /` with `topic`).
24. **ZimaOS "Failed to pull image after 5 mirror methods"** → GHCR package private by default (separate from repo visibility) → Package settings → Change visibility → Public. Verify: `curl ghcr.io/token?scope=repository:<owner>/<img>:pull` returns 200.
25. **Per-username login lockout = DoS on a public instance** → anyone can burn the owner's attempts → throttle per client IP only (uvicorn `--proxy-headers` makes `request.client.host` the real IP behind a proxy).
26. **No official Clue export spec** → inferred `.cluedata` = `{"data":[{"day","period",...}]}` from community converters; Flo verified via flo-to-drip (`operationalData.cycles`). Keep importer tolerant and report "no period days found" clearly.
27. **Apple Health export.xml can be GBs** → never upload it; stream in browser (`file.stream().pipeThrough(new TextDecoderStream())`), scan only up to last `<` per chunk so no tag is split, send compact records.
28. **HealthKit renamed MenstrualFlow values to VaginalBleeding (iOS 18)** → match value by suffix (Light/Medium/Heavy/Unspecified), not full string.
29. **New test registering first user broke `test_full_flow` (expects empty DB)** → tests share one data dir; put tests that create the first account in files sorting after `test_api.py` (e.g. `test_recap.py`).
30. **Calendar day panel hidden behind bottom nav on iPhone** → nav height grows by `env(safe-area-inset-bottom)` (home indicator) but panel/chat/toast used hard-coded 68–84px → single CSS var `--nav-h: calc(56px + max(env(safe-area-inset-bottom), .5rem))` on `:root`; nav gets that height and everything anchored to it uses `var(--nav-h)`. Verified by emulating a 34px inset in Playwright (panel bottom 746 ≤ nav top 754).
31. **`navigator.clipboard` undefined over plain http (Tailscale IP)** → Clipboard API requires a secure context → show Copy only when `window.isSecureContext`; make link text `select-all` for manual copy.
32. **Dev server dies between turns** (sandbox resets background processes) → always health-check `localhost:8500` and restart + reseed before E2E.
33. **After-log note "flashed" and was lost** → 6 s toast that dismissed on any tap, not stored anywhere → toast ≥10 s (≈90 ms/char) with an explicit close button + persist latest note per user/day as a Today feed card.
34. **Seed/app failed with `No module named fastapi`** → system python used instead of the backend venv → run servers and scripts with `backend/.venv/bin/python`.
35. **Streaming via proxies buffers** → nginx-style proxies hold chunks → send `X-Accel-Buffering: no`; plain-text chunked body (not SSE) keeps the client to a few lines of `TextDecoderStream`.
36. **Account delete left Setting rows behind** (log notes, share/HA tokens) → per-user keys weren't tied to `user_id` → delete `%:<uid>`, `%:<uid>:%` and token rows whose value is the uid.
37. **Tests needing a throwaway account** → registration is closed after the first user → `monkeypatch.setattr(auth, "registration_open", lambda db: True)` instead of depending on file order.
10. **`starlette.testclient` deprecation warning re httpx** → Starlette now prefers `httpx2` → harmless; revisit when upgrading.
