# Security

## Overview

Runs AI‑generated code in a sandbox with layered protections:

- **Execution isolation**: `SecureRunner` sandbox with temp working directory and cleanup on exit
- **Runtime guards**: Block eval/exec/compile, subprocess, dangerous imports (ctypes, pickle, marshal, etc.)
- **Network controls**: Egress blocked by default (socket overrides); explicit opt-in via `--allow-network` or `--unsafe`
- **Filesystem mediation**: Guarded file operations with path validation limited to temp scope
- **Resource limits**: POSIX rlimits (CPU/memory/file size); Windows Job Objects when pywin32 available
- **Environment scrubbing**: Sensitive pattern filtering and controlled rebuild
- **Dynamic validation**: Runtime canaries validate static heuristics in every security audit
- **CI integration**: Mandatory security audit integrated in CI pipeline with JSON artifacts and pass/fail gating
- **Failure transparency**: Banner honesty check ensures security claims match enforced controls
- **Opt-out**: `--unsafe` mode (loudly logged, reduces guardrails for comparative analysis only)

For complete threat model, enforcement details, and verification procedures, see the full security documentation below.

---

--8<-- "SAFETY.md"

