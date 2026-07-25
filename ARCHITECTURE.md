NovaGraph Common Architecture
=============================

Overview
--------
Input File -> Block Manager -> Feature Extraction -> Router -> Engines ->
Pattern Selection -> Entropy Coding -> NOVA File

Components
----------
- Block Manager: splits files into blocks with adjustable block size.
- Feature Extraction: entropy, histograms, transition matrices, graph density.
- Router: queries engines with estimates (size/cost/confidence) and selects
  best representation per block.
- Engines: pluggable modules implementing a common interface. May be Python
  prototypes (Lab) or Rust production engines (Engine).
- Entropy Coders: modular (Huffman first, ANS later).
- NOVA File: stable container format with header, version, metadata, merkle.

Plugin contract (summary)
-------------------------
Each engine must provide:
- `engine_id` (unique identifier)
- `analyze(block: &[u8]) -> EngineEstimate` (returns estimated size, cost)
- `compress(block: &[u8]) -> CompressedBlob`
- `decompress(blob: &[u8]) -> Vec<u8>`
- Deterministic behavior and byte-perfect restoration

Benchmarking & Profiling
------------------------
- Stage timings for each phase
- Per-engine counters and CPU/memory stats
- Output: JSON, CSV, Markdown

Roadmap
-------
See ROADMAP.md for versioned milestones.
