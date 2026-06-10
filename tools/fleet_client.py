"""LLM client with a graceful provider fallback chain.

Public API (unchanged from the original fleet-only client):

    from fleet_client import call, call_json, call_vision, ENDPOINTS

    text = call("llama3.1:8b", "Say hi.", endpoint=ENDPOINTS["sam"])
    data = call_json("llama3.1:8b", prompt, endpoint=ENDPOINTS["sam"])
    alt  = call_vision("Describe this.", image_b64)

The `model` / `endpoint` arguments are now *hints*: they are honored verbatim
when the resolved provider is an Ollama endpoint that actually has the model,
and ignored when the chain resolves to a hosted API (which has its own model).

Provider resolution order (first available wins, cached per process):

  1. tools/providers.json        — explicit config (gitignored; see
                                   providers.json.example). Ordered list of
                                   {type, base_url, model, api_key_env}.
  2. Environment auto-detect     — ANTHROPIC_API_KEY → Anthropic Messages API;
                                   OPENAI_API_KEY → OpenAI-compatible chat
                                   completions (OPENAI_BASE_URL overridable);
                                   OLLAMA_HOST → that Ollama endpoint.
  3. Local Ollama probe          — http://localhost:11434 (~1s timeout),
                                   preferring llama3.1:8b > qwen2.5-coder:14b
                                   > qwen3:8b > whatever is installed.
  4. Author's Tailscale fleet    — the ENDPOINTS table below. Harmless for
                                   strangers (short probe timeout, fails fast).
  5. Nothing                     — NoProviderError + one friendly stderr hint.
                                   Importers already catch this and fall back
                                   to deterministic output.

Stdlib only (urllib) — the importer suite stays zero-deps. No native JSON
mode; we prompt for JSON and validate the parse. Per fleet eval notes:
single-pass only, never "revise".
"""
from __future__ import annotations
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# ── Author's fleet (last-resort fallback; Tailscale is the perimeter) ──
ENDPOINTS = {
    "sam":    "http://100.127.46.63:11434",   # llama3.1:8b — structured JSON / classification
    "archie": "http://100.103.192.41:11434",  # qwen2.5-coder:14b — code parsing
    "lenny":  "http://100.78.179.55:11434",   # gemma3:27b / qwen3-coder:30b — design, code
    "mbp":    "http://100.95.59.11:11434",    # qwen3-coder:30b — code-gen fallback
}

LOCAL_OLLAMA = "http://localhost:11434"
CONFIG_PATH = Path(__file__).resolve().parent / "providers.json"

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # cheap default for normalization
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
PREFERRED_OLLAMA = ("llama3.1:8b", "qwen2.5-coder:14b", "qwen3:8b")
# Heuristic substrings for vision-capable Ollama models.
VISION_HINTS = ("llava", "vision", "gemma3", "qwen2.5vl", "qwen2-vl", "qwen3-vl",
                "moondream", "minicpm-v", "bakllava", "pixtral")

JSON_SUFFIX = '\n\nReturn ONLY valid JSON. No prose, no markdown fences, no explanation.'

THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

PROBE_TIMEOUT = 1.5  # seconds — connect/read budget for /api/tags availability checks

HINT = """\
[fleet_client] No LLM provider available. To enable LLM-assisted features, do ONE of:
  - export ANTHROPIC_API_KEY=sk-ant-...   (uses Claude Haiku via api.anthropic.com)
  - export OPENAI_API_KEY=sk-...          (uses gpt-4o-mini; OPENAI_BASE_URL to point elsewhere)
  - install Ollama (https://ollama.com) and `ollama pull llama3.1:8b`
  - or copy tools/providers.json.example to tools/providers.json and edit it
Most importers also accept --no-llm for deterministic output with no model at all.
"""


class NoProviderError(RuntimeError):
    """No LLM provider could be resolved. Importers catch this (as Exception)
    and fall back to raw/deterministic output."""


_hint_printed = False


def _print_hint_once() -> None:
    global _hint_printed
    if not _hint_printed:
        sys.stderr.write(HINT)
        _hint_printed = True


# ── HTTP helpers ──

def _http_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


_TAGS_CACHE: dict[str, list[str] | None] = {}


def _ollama_tags(base_url: str) -> list[str] | None:
    """GET /api/tags with a short timeout. Returns model names, or None if
    the endpoint is unreachable. Cached per process (success AND failure)."""
    if base_url in _TAGS_CACHE:
        return _TAGS_CACHE[base_url]
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            body = json.loads(resp.read())
        names = [m.get("name", "") for m in body.get("models", []) if m.get("name")]
        _TAGS_CACHE[base_url] = names
    except Exception:
        _TAGS_CACHE[base_url] = None
    return _TAGS_CACHE[base_url]


def _match_tag(requested: str, tags: list[str]) -> str | None:
    """Exact tag match, then base-name match (llama3.1:8b ~ llama3.1:latest)."""
    if requested in tags:
        return requested
    base = requested.split(":")[0]
    for t in tags:
        if t.split(":")[0] == base:
            return t
    return None


def _pick_text_model(tags: list[str], requested: str | None, pinned: str | None) -> str | None:
    if pinned:
        return pinned  # explicit config wins, even if not in tags (404s → next candidate)
    if requested:
        m = _match_tag(requested, tags)
        if m:
            return m
    for pref in PREFERRED_OLLAMA:
        m = _match_tag(pref, tags)
        if m:
            return m
    return tags[0] if tags else None


def _pick_vision_model(tags: list[str], requested: str | None, pinned: str | None) -> str | None:
    if pinned:
        return pinned
    if requested:
        m = _match_tag(requested, tags)
        if m:
            return m
    for t in tags:
        low = t.lower()
        if any(h in low for h in VISION_HINTS):
            return t
    return None


# ── provider resolution ──

def _normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if url and "://" not in url:
        url = "http://" + url
    return url


def _config_providers() -> list[dict]:
    """Parse tools/providers.json. Accepts a bare list or {"providers": [...]}."""
    if not CONFIG_PATH.exists():
        return []
    try:
        raw = json.loads(CONFIG_PATH.read_text())
    except Exception as e:
        sys.stderr.write(f"[fleet_client] WARN: could not parse {CONFIG_PATH.name}: {e}\n")
        return []
    entries = raw.get("providers", []) if isinstance(raw, dict) else raw
    out: list[dict] = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        ptype = ent.get("type")
        if ptype not in ("ollama", "openai", "anthropic"):
            continue
        api_key = None
        key_env = ent.get("api_key_env")
        if ptype in ("openai", "anthropic"):
            api_key = os.environ.get(key_env or "", "") if key_env else ""
            if not api_key:
                sys.stderr.write(
                    f"[fleet_client] WARN: providers.json {ptype} entry skipped — "
                    f"env var {key_env or '(api_key_env unset)'} is empty.\n")
                continue
        base = _normalize_url(ent.get("base_url") or "")
        if not base:
            base = {"ollama": LOCAL_OLLAMA,
                    "openai": "https://api.openai.com/v1",
                    "anthropic": "https://api.anthropic.com"}[ptype]
        out.append({
            "type": ptype,
            "base_url": base,
            "model": ent.get("model"),
            "vision_model": ent.get("vision_model"),
            "api_key": api_key,
            "label": f"config:{ptype}({ent.get('model') or 'auto'})",
        })
    return out


def candidates(preferred_endpoint: str | None = None) -> list[dict]:
    """Ordered provider candidates per the resolution chain. Availability is
    checked lazily at call time (Ollama endpoints get a short /api/tags probe).
    `preferred_endpoint` (a caller-passed Ollama URL) is tried first within
    the fleet tier, preserving the original per-host routing."""
    cands: list[dict] = []

    # 1. Explicit config.
    cands.extend(_config_providers())

    # 2. Environment auto-detect.
    if os.environ.get("ANTHROPIC_API_KEY"):
        cands.append({"type": "anthropic", "base_url": "https://api.anthropic.com",
                      "model": DEFAULT_ANTHROPIC_MODEL, "vision_model": None,
                      "api_key": os.environ["ANTHROPIC_API_KEY"], "label": "env:anthropic"})
    if os.environ.get("OPENAI_API_KEY"):
        cands.append({"type": "openai",
                      "base_url": _normalize_url(os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"),
                      "model": DEFAULT_OPENAI_MODEL, "vision_model": None,
                      "api_key": os.environ["OPENAI_API_KEY"], "label": "env:openai"})
    if os.environ.get("OLLAMA_HOST"):
        cands.append({"type": "ollama", "base_url": _normalize_url(os.environ["OLLAMA_HOST"]),
                      "model": None, "vision_model": None, "api_key": None,
                      "label": "env:ollama"})

    # 3. Local Ollama probe.
    cands.append({"type": "ollama", "base_url": LOCAL_OLLAMA, "model": None,
                  "vision_model": None, "api_key": None, "label": "localhost:ollama"})

    # 4. Author's fleet — caller's requested endpoint first, then the rest.
    fleet_urls = list(ENDPOINTS.values())
    if preferred_endpoint and preferred_endpoint in fleet_urls:
        fleet_urls.remove(preferred_endpoint)
        fleet_urls.insert(0, preferred_endpoint)
    elif preferred_endpoint:
        fleet_urls.insert(0, preferred_endpoint)
    seen = {c["base_url"] for c in cands if c["type"] == "ollama"}
    for url in fleet_urls:
        if url in seen:
            continue
        cands.append({"type": "ollama", "base_url": url, "model": None,
                      "vision_model": None, "api_key": None, "label": f"fleet:{url}"})
    return cands


def resolve_provider(vision: bool = False, preferred_endpoint: str | None = None,
                     requested_model: str | None = None) -> dict:
    """Walk the chain and return the first AVAILABLE provider (with a usable
    model resolved for Ollama endpoints). Raises NoProviderError if none.
    Diagnostic / pre-flight helper; call()/call_vision() do the same walk
    internally but also fall through on mid-call errors."""
    for cand in candidates(preferred_endpoint):
        if cand["type"] in ("anthropic", "openai"):
            return cand
        tags = _ollama_tags(cand["base_url"])
        if tags is None:
            continue
        picker = _pick_vision_model if vision else _pick_text_model
        model = picker(tags, requested_model, cand.get("vision_model" if vision else "model"))
        if model:
            return {**cand, "model": model}
    _print_hint_once()
    raise NoProviderError("no LLM provider available"
                          + (" with vision support" if vision else "")
                          + " (see hint above, or use --no-llm)")


# ── per-provider call shims ──

def _call_ollama(base_url: str, model: str, prompt: str, *, timeout: int,
                 temperature: float, system: str | None,
                 images: list[str] | None = None) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system
    if images:
        payload["images"] = images
    body = _http_post_json(f"{base_url}/api/generate", payload, {}, timeout)
    return body.get("response", "")


def _sniff_media_type(image_b64: str) -> str:
    import base64 as _b64
    try:
        head = _b64.b64decode(image_b64[:32] + "==")
    except Exception:
        return "image/jpeg"
    if head.startswith(b"\x89PNG"):
        return "image/png"
    if head.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if head.startswith(b"GIF8"):
        return "image/gif"
    if head.startswith(b"RIFF"):
        return "image/webp"
    return "image/jpeg"


def _call_anthropic(cand: dict, prompt: str, *, timeout: int, temperature: float,
                    system: str | None, image_b64: str | None = None) -> str:
    if image_b64:
        content: Any = [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": _sniff_media_type(image_b64),
                                         "data": image_b64}},
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt
    payload: dict[str, Any] = {
        "model": cand["model"] or DEFAULT_ANTHROPIC_MODEL,
        "max_tokens": 2048,
        "temperature": temperature,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        payload["system"] = system
    body = _http_post_json(
        f"{cand['base_url']}/v1/messages", payload,
        {"x-api-key": cand["api_key"], "anthropic-version": "2023-06-01"},
        timeout,
    )
    return "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")


def _call_openai(cand: dict, prompt: str, *, timeout: int, temperature: float,
                 system: str | None, image_b64: str | None = None) -> str:
    if image_b64:
        mt = _sniff_media_type(image_b64)
        user_content: Any = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mt};base64,{image_b64}"}},
        ]
    else:
        user_content = prompt
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_content})
    payload = {
        "model": cand["model"] or DEFAULT_OPENAI_MODEL,
        "temperature": temperature,
        "messages": messages,
    }
    body = _http_post_json(
        f"{cand['base_url']}/chat/completions", payload,
        {"Authorization": f"Bearer {cand['api_key']}"},
        timeout,
    )
    return body["choices"][0]["message"]["content"] or ""


# ── public API ──

def _walk_and_call(prompt: str, *, requested_model: str | None, endpoint: str | None,
                   timeout: int, temperature: float, system: str | None,
                   image_b64: str | None) -> str:
    vision = image_b64 is not None
    errors: list[str] = []
    for cand in candidates(endpoint):
        try:
            if cand["type"] == "anthropic":
                text = _call_anthropic(cand, prompt, timeout=timeout,
                                       temperature=temperature, system=system,
                                       image_b64=image_b64)
            elif cand["type"] == "openai":
                text = _call_openai(cand, prompt, timeout=timeout,
                                    temperature=temperature, system=system,
                                    image_b64=image_b64)
            else:  # ollama (config / env / localhost / fleet)
                tags = _ollama_tags(cand["base_url"])
                if tags is None:
                    continue  # unreachable — no error worth reporting
                picker = _pick_vision_model if vision else _pick_text_model
                model = picker(tags, requested_model,
                               cand.get("vision_model" if vision else "model"))
                if not model:
                    errors.append(f"{cand['label']}: no "
                                  f"{'vision-capable ' if vision else ''}model available")
                    continue
                text = _call_ollama(cand["base_url"], model, prompt, timeout=timeout,
                                    temperature=temperature, system=system,
                                    images=[image_b64] if image_b64 else None)
            return THINK_BLOCK.sub("", text).strip()
        except (NoProviderError, KeyboardInterrupt):
            raise
        except Exception as e:
            errors.append(f"{cand['label']}: {e}")
            continue
    _print_hint_once()
    detail = ("; ".join(errors[-3:])) or "no providers reachable"
    raise NoProviderError(
        f"no LLM provider {'with vision support ' if vision else ''}available ({detail})")


def call(model: str, prompt: str, *, endpoint: str | None = None, timeout: int = 180,
         temperature: float = 0.2, system: str | None = None) -> str:
    """Text generation through the provider chain. `model` and `endpoint` are
    hints honored when an Ollama endpoint serves the call; hosted APIs use
    their own configured model."""
    return _walk_and_call(prompt, requested_model=model, endpoint=endpoint,
                          timeout=timeout, temperature=temperature, system=system,
                          image_b64=None)


def call_vision(prompt: str, image_b64: str, *, model: str | None = None,
                endpoint: str | None = None, timeout: int = 120,
                temperature: float = 0.2) -> str:
    """Vision call (single base64 image + prompt) through the same chain.
    Anthropic/OpenAI accept the image natively; Ollama endpoints need a
    vision-capable model installed. Raises NoProviderError otherwise."""
    return _walk_and_call(prompt, requested_model=model, endpoint=endpoint,
                          timeout=timeout, temperature=temperature, system=None,
                          image_b64=image_b64)


def _extract_json(text: str) -> Any:
    text = FENCE.sub("", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: grab the largest {...} or [...] block.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Model did not return valid JSON. Got:\n{text[:500]}")


def call_json(model: str, prompt: str, *, endpoint: str | None = None, timeout: int = 180,
              temperature: float = 0.1, system: str | None = None,
              required_keys: list[str] | None = None) -> Any:
    """Call a model and parse JSON from its response.

    Single-pass by design. If parsing fails, raises — caller decides whether
    to retry with a *different* prompt (never "please fix your JSON").
    """
    raw = call(model, prompt + JSON_SUFFIX, endpoint=endpoint,
               timeout=timeout, temperature=temperature, system=system)
    data = _extract_json(raw)
    if required_keys and isinstance(data, dict):
        missing = [k for k in required_keys if k not in data]
        if missing:
            raise ValueError(f"Missing required keys {missing}. Got: {list(data.keys())}")
    return data


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Provider-chain diagnostic / ping")
    ap.add_argument("--probe-only", action="store_true", help="resolve, don't generate")
    ap.add_argument("--vision", action="store_true", help="resolve a vision-capable provider")
    ap.add_argument("--model", default=None, help="requested model hint")
    ap.add_argument("--host", default=None, choices=list(ENDPOINTS),
                    help="preferred fleet endpoint hint")
    args = ap.parse_args()
    ep = ENDPOINTS[args.host] if args.host else None
    print("Resolution chain:", file=sys.stderr)
    for c in candidates(ep):
        print(f"  - {c['label']:24s} {c['type']:9s} {c['base_url']}", file=sys.stderr)
    try:
        p = resolve_provider(vision=args.vision, preferred_endpoint=ep,
                             requested_model=args.model)
        print(f"Resolved: {p['label']} → {p['type']} model={p['model']} at {p['base_url']}",
              file=sys.stderr)
    except NoProviderError as e:
        print(f"Resolved: NOTHING — {e}", file=sys.stderr)
        sys.exit(1)
    if not args.probe_only and not args.vision:
        print(call(args.model or "llama3.1:8b",
                   "Reply with exactly the word: pong", endpoint=ep))
