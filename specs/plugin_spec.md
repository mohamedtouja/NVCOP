NovaGraph Plugin Specification
==============================

Purpose
-------
Define a minimal, language-agnostic plugin API for compression engines.

Engine contract
---------------
- `engine_id: str` — unique engine identifier
- `analyze(block_bytes: bytes) -> EngineEstimate`
  - `estimated_size_bytes: int`
  - `estimated_cpu_ms: float`
  - `estimated_memory_bytes: int`
  - `confidence: float` (0.0 - 1.0)
- `compress(block_bytes: bytes, params: dict) -> CompressedBlob`
  - `CompressedBlob` includes `engine_id`, `payload`, `metadata`
- `decompress(blob: CompressedBlob) -> bytes`

EngineEstimate
--------------
- `estimated_size_bytes`
- `estimated_cpu_ms`
- `estimated_memory_bytes`
- `confidence`
- `explain` optional human-readable note

Interoperability
----------------
- The binary NOVA format stores the `engine_id` per block so Rust and Python
  implementations can interoperate as long as they comply with encoding.
- Engine metadata must be JSON-serializable and validated during decompression.

Versioning
----------
- Start with `plugin-spec-v0.1`.
- Any incompatible interface change requires a spec bump and migration notes.
