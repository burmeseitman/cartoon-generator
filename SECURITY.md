# Security Notes

This document covers the security considerations for the Cartoon Generator project.

## Dependencies & Known Vulnerabilities

| Package | Current Version | Required Version | Vulnerability | CVE | Status |
|---|---|---|---|---|---|
| `requests` | 2.32.5 | >=2.32.3,<3.0.0 | Insecure temp file reuse | CVE-2026-25645 | **FIXED** — pinned `>=2.32.3` in requirements.txt |
| `Pillow` | (optional) | >=10.0.0 | — | — | No known vulnerabilities |
| `openai` | (optional) | — | — | — | No known vulnerabilities |

### Dependency Management

Run security scans before each release:
```bash
pip install safety
safety check --full-report
```

Or use `pip-audit`:
```bash
pip install pip-audit
pip audit
```

## Code-Level Security Measures

### 1. URL Validation (SSRF Prevention)
- All URLs from external sources are validated with `is_safe_url()` before use
- Only `http://` and `https://` schemes are allowed
- Prevents `file://`, `ftp://`, and other dangerous schemes

### 2. Path Traversal Prevention
- Generated filenames are validated to contain no `/`, `\`, or leading `.`
- Final file paths are resolved and verified to stay within `CARTOON_DIR`
- Configurable `IMAGE_FILENAME_FORMAT` is sanitized through `sanitize_filename()`

### 3. Input Sanitization
- RSS feed content (titles, descriptions) is cleaned of control characters
- HTML entities are decoded safely
- Control characters (`\x00-\x08`, `\x0b`, `\x0c`, `\x0e-\x1f`) are stripped
- Prevents log injection and data corruption

### 4. File Size Limits
- `history.json` is capped at 1 MB to prevent disk exhaustion DoS
- Article text fields are truncated to 500 characters
- Filenames are truncated to 50 characters

### 5. Timeout Protection
- All HTTP requests (`urlopen`, `requests.get`) have explicit timeouts
- RSS/NewsAPI calls: 30s timeout
- Pollinations.ai image download: 60s timeout
- Gemini API image generation: 90s timeout (slower due to image generation latency)
- Prevents hanging connections and resource exhaustion

### 6. Image Validation
- Generated images are validated with Pillow's `Image.verify()` before saving
- Falls back to raw save only if Pillow is unavailable (logged as warning)

## Threat Model

| Threat | Mitigation |
|---|---|
| SSRF via malicious news source URL | `is_safe_url()` validation + scheme whitelist |
| Path traversal via crafted filename | Filename sanitization + resolved path verification |
| Log injection via RSS content | Control character stripping |
| Disk DoS via oversized history file | 1 MB size limit on `history.json` |
| Hanging on slow/unresponsive servers | Explicit timeouts on all HTTP calls (30s–90s depending on endpoint) |
| Malicious image payload | Pillow `verify()` before writing to disk |
| Credential theft via `.env` file | `.gitignore` excludes `.env`; never committed |

## Secrets Management

- API keys are loaded exclusively from environment variables or `.env` file
- No secrets are hardcoded in source code
- `.env` is listed in `.gitignore`
- `.env.example` contains placeholder values only

## Running as a Background Job

When deploying, consider these additional hardening steps:

1. **Run as a non-root user** — never run the background service as root
2. **Use a virtual environment** — isolate dependencies per project
3. **Restrict output directory permissions**:
   ```bash
   chmod 750 output/
   chmod 640 output/history.json
   ```
4. **Use systemd with security directives**:
   ```ini
   [Service]
   ProtectSystem=strict
   ProtectHome=true
   NoNewPrivileges=true
   PrivateTmp=true
   ```
