# Launch Assets

## GitHub short description

Minimal FastAPI backend for code-analysis request intake, built as an honest experimental MVP.

## GitHub About text

CodeShield AI is a backend-only FastAPI MVP for code-analysis intake. One endpoint, strict scope, no fake demos: submit code, get a request ID, extend from there.

## Twitter/X launch post

Shipped: CodeShield AI (experimental MVP)

It is intentionally small:
- FastAPI backend only
- `POST /api/v1/analyze`
- input validation
- `request_id` + `pending` response

No fake dashboard. No fake AI claims. No "enterprise-ready" language.
Just a clean, runnable base for building a real code-analysis service in public.

Repo: [add-link]

## LinkedIn launch post

I just open-sourced an early MVP called CodeShield AI.

It is a backend-only FastAPI project with a deliberately small scope: a single analysis intake endpoint that validates code input and returns a request ID.

I removed fake benchmarks and non-runnable demo layers, then kept only what can run and be verified today.

If you prefer clean starting points over inflated claims, this repo is built for that style.

Repo: [add-link]

## Product Hunt style tagline

An honest FastAPI MVP for code-analysis intake - small, runnable, and built to evolve in public.

## Hacker-facing paragraph

Most repos in this category overpromise. This one starts with a narrow contract that actually runs, then leaves room for real engineering work: result retrieval, persistence, worker orchestration, and auth. If you like small systems with explicit scope and clear extension paths, this is a solid base to fork or contribute to.
