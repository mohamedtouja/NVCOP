NovaGraph-Engine
=================

Purpose
-------
NovaGraph-Engine is the high-performance Rust implementation of NovaGraph.
Production-grade engine, optimized for parallelism, memory-efficiency, and
stable .nova artifacts.

Notes
-----
- The existing workspace `novagraph-rust` can be migrated into this repository
  or used as the starting point for `NovaGraph-Engine`.
- Implement plugin interfaces using Rust traits under `src/engines`.

Getting started
---------------
- Build with `cargo build`.
- Benchmarks and profiling harness live under `benchmark/`.
