use novagraph_rust::{NovaCompressor, NovaDecompressor, engines::{fractal::FractalEngine, spectral::SpectralEngine}};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Write;

#[test]
fn fractal_engine_detects_repeats() {
    let engine = FractalEngine::new();
    let data = b"ABCABCABCABC";
    let analysis = engine.analyze(data);
    assert!(analysis.score > 1.0);
}

#[test]
fn spectral_engine_scores_data() {
    let engine = SpectralEngine::new();
    let data = b"The quick brown fox jumps over the lazy dog.";
    let analysis = engine.analyze(data);
    assert!(analysis.score >= 0.0);
}

#[test]
fn fractal_compressor_roundtrip_preserves_bytes() {
    let temp_dir = std::env::temp_dir().join("novagraph_rust_phase4_test");
    let _ = fs::remove_dir_all(&temp_dir);
    fs::create_dir_all(&temp_dir).unwrap();

    let input_path = temp_dir.join("sample.bin");
    let compressed_path = temp_dir.join("sample.nova");
    let output_path = temp_dir.join("sample.restored.bin");

    let payload = b"Phase 4 fractal and spectral engine roundtrip test.";
    let mut input_file = File::create(&input_path).unwrap();
    input_file.write_all(payload).unwrap();

    let original_hash = Sha256::digest(payload);

    let compressor = NovaCompressor::new_fractal(1024);
    compressor.compress_file(&input_path, &compressed_path).unwrap();

    let decompressor = NovaDecompressor::new();
    decompressor.decompress_file(&compressed_path, &output_path).unwrap();

    let restored = fs::read(&output_path).unwrap();
    let restored_hash = Sha256::digest(&restored);

    assert_eq!(original_hash.as_slice(), restored_hash.as_slice());
    assert_eq!(payload.as_slice(), restored.as_slice());
}
