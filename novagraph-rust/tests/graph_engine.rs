use novagraph_rust::{NovaCompressor, NovaDecompressor, engines::graph::GraphEngine};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Write;
use std::path::PathBuf;

#[test]
fn graph_engine_returns_analysis_score() {
    let engine = GraphEngine::new();
    let data = b"ABABABABABABABA pattern repetition test.";
    let result = engine.analyze(data);

    assert!(result.score > 0.0);
}

#[test]
fn graph_compressor_roundtrip_still_preserves_bytes() {
    let temp_dir = std::env::temp_dir().join("novagraph_rust_phase3_test");
    let _ = fs::remove_dir_all(&temp_dir);
    fs::create_dir_all(&temp_dir).unwrap();

    let input_path = temp_dir.join("sample.bin");
    let compressed_path = temp_dir.join("sample.nova");
    let output_path = temp_dir.join("sample.restored.bin");

    let payload = b"NovaGraph Phase 3 graph engine compression roundtrip test.";
    let mut input_file = File::create(&input_path).unwrap();
    input_file.write_all(payload).unwrap();

    let original_hash = Sha256::digest(payload);

    let compressor = NovaCompressor::new_graph(1024);
    compressor.compress_file(&input_path, &compressed_path).unwrap();

    let decompressor = NovaDecompressor::new();
    decompressor.decompress_file(&compressed_path, &output_path).unwrap();

    let restored = fs::read(&output_path).unwrap();
    let restored_hash = Sha256::digest(&restored);

    assert_eq!(original_hash.as_slice(), restored_hash.as_slice());
    assert_eq!(payload.as_slice(), restored.as_slice());
}
