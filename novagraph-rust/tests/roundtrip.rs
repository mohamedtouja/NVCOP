use novagraph_rust::{NovaCompressor, NovaDecompressor};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Write;
use std::path::PathBuf;

mod test_helpers {
    use std::env;
    use std::fs;
    use std::path::PathBuf;

    pub fn setup_temp() -> std::io::Result<PathBuf> {
        let mut temp_dir = env::temp_dir();
        temp_dir.push("novagraph_rust_phase1_test");
        if temp_dir.exists() {
            fs::remove_dir_all(&temp_dir)?;
        }
        fs::create_dir_all(&temp_dir)?;
        Ok(temp_dir)
    }
}

#[test]
fn roundtrip_compress_decompress_preserves_bytes() {
    let temp_dir = std::env::temp_dir().join("novagraph_rust_phase1_test");
    let input_path = temp_dir.join("sample.bin");
    let compressed_path = temp_dir.join("sample.nova");
    let output_path = temp_dir.join("sample.restored.bin");

    let payload = b"NovaGraph experimental lossless compression test data.";
    let mut input_file = File::create(&input_path).unwrap();
    input_file.write_all(payload).unwrap();

    let original_hash = Sha256::digest(payload);

    let compressor = NovaCompressor::new(1024);
    compressor.compress_file(&input_path, &compressed_path).unwrap();

    let decompressor = NovaDecompressor::new();
    decompressor.decompress_file(&compressed_path, &output_path).unwrap();

    let restored = fs::read(&output_path).unwrap();
    let restored_hash = Sha256::digest(&restored);

    assert_eq!(original_hash.as_slice(), restored_hash.as_slice());
    assert_eq!(payload.as_slice(), restored.as_slice());
}
