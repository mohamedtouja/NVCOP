NovaGraph Roadmap
=================

Version 0.1 - Core framework
- NOVA container format
- Block manager, feature extraction
- Plugin interfaces (Python and Rust)
- Basic entropy coder (Huffman)
- Benchmark harness

Version 0.2 - Graph Engine
- Implement Graph Engine in Python (Lab)
- Benchmark and profile
- Port to Rust if beneficial

Version 0.3 - Fractal Engine
Version 0.4 - Spectral Engine
Version 0.5 - Combinatorial Engine
Version 0.6 - ML optimizer (compression-time only)
Version 0.7 - Optional GPU acceleration
Version 1.0 - Stable release

Notes
-----
- Every engine must be benchmarked in Lab before porting.
- Keep interfaces stable and document changes in CHANGELOG.md.
