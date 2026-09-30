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
10. **`starlette.testclient` deprecation warning re httpx** → Starlette now prefers `httpx2` → harmless; revisit when upgrading.
