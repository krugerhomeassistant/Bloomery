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
10. **`starlette.testclient` deprecation warning re httpx** → Starlette now prefers `httpx2` → harmless; revisit when upgrading.
