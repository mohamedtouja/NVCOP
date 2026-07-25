use std::fs::{self, File};
use std::io::{self, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

use brotli::{CompressorWriter, Decompressor};
use csv::Writer;
use flate2::read::{GzDecoder, ZlibDecoder};
use flate2::write::{GzEncoder, ZlibEncoder};
use flate2::Compression;
use serde::Serialize;
use sysinfo::{Pid, PidExt, ProcessExt, System, SystemExt};
use zstd::stream::{copy_decode, copy_encode};

use crate::core::compressor::CompressionReport;
use crate::core::decompressor::DecompressionReport;
use crate::core::{NovaCompressor, NovaDecompressor};

#[derive(Serialize)]
pub struct AlgorithmResult {
    pub algorithm: String,
    pub compressed_size: u64,
    pub ratio: f64,
    pub compress_ms: f64,
    pub decompress_ms: f64,
    pub compress_mb_s: f64,
    pub decompress_mb_s: f64,
    pub memory_bytes: u64,
    pub cpu_percent: f32,
}

#[derive(Serialize)]
pub struct FileBenchmark {
    pub file_name: String,
    pub original_size: u64,
    pub nova_report: CompressionReport,
    pub nova_decompression: DecompressionReport,
    pub algorithm_results: Vec<AlgorithmResult>,
}

fn current_process_stats() -> (u64, f32) {
    let mut sys = System::new();
    let pid = Pid::from(std::process::id());
    sys.refresh_process(pid);
    if let Some(process) = sys.process(pid) {
        (process.memory() * 1024, process.cpu_usage())
    } else {
        (0, 0.0)
    }
}

fn make_sample_files(base: &Path) -> io::Result<Vec<PathBuf>> {
    fs::create_dir_all(base)?;
    let mut files = Vec::new();

    let repeated = base.join("repeated.bin");
    let mut repeated_file = File::create(&repeated)?;
    repeated_file.write_all(&b"ABC12345".repeat(524288 / 8))?;
    files.push(repeated);

    let random = base.join("random.bin");
    let mut random_file = File::create(&random)?;
    random_file.write_all(&pseudo_random_bytes(4 * 1024 * 1024))?;
    files.push(random);

    let text = base.join("text.txt");
    let mut text_file = File::create(&text)?;
    text_file.write_all(&b"the quick brown fox jumps over the lazy dog\n".repeat(1024 * 4))?;
    files.push(text);

    Ok(files)
}

fn pseudo_random_bytes(size: usize) -> Vec<u8> {
    let mut buffer = Vec::with_capacity(size);
    let mut state = 0x12345678u32;
    for _ in 0..size {
        state = state.wrapping_mul(1664525).wrapping_add(1013904223);
        buffer.push((state >> 24) as u8);
    }
    buffer
}

fn compress_zlib(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data)?;
    encoder.finish()
}

fn decompress_zlib(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut decoder = ZlibDecoder::new(data);
    let mut output = Vec::new();
    decoder.read_to_end(&mut output)?;
    Ok(output)
}

fn compress_gzip(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data)?;
    encoder.finish()
}

fn decompress_gzip(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut decoder = GzDecoder::new(data);
    let mut output = Vec::new();
    decoder.read_to_end(&mut output)?;
    Ok(output)
}

fn compress_brotli(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut buffer = Vec::new();
    {
        let mut encoder = CompressorWriter::new(&mut buffer, 4096, 5, 22);
        encoder.write_all(data)?;
    }
    Ok(buffer)
}

fn decompress_brotli(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut decoder = Decompressor::new(data, 4096);
    let mut output = Vec::new();
    decoder.read_to_end(&mut output)?;
    Ok(output)
}

fn compress_zstd(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut output = Vec::new();
    copy_encode(data, &mut output, 0)?;
    Ok(output)
}

fn decompress_zstd(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut output = Vec::new();
    copy_decode(data, &mut output)?;
    Ok(output)
}

fn measure_algorithm<F, G>(
    name: &str,
    data: &[u8],
    encode: F,
    decode: G,
) -> io::Result<AlgorithmResult>
where
    F: Fn(&[u8]) -> io::Result<Vec<u8>>,
    G: Fn(&[u8]) -> io::Result<Vec<u8>>,
{
    let original_size = data.len() as u64;
    let start_stats = current_process_stats();
    let compress_start = Instant::now();
    let compressed = encode(data)?;
    let compress_ms = compress_start.elapsed().as_secs_f64() * 1000.0;
    let decompress_start = Instant::now();
    let decompressed = decode(&compressed)?;
    let decompress_ms = decompress_start.elapsed().as_secs_f64() * 1000.0;
    let end_stats = current_process_stats();

    if decompressed != data {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "Decompressed data did not match original",
        ));
    }

    let compressed_size = compressed.len() as u64;
    Ok(AlgorithmResult {
        algorithm: name.to_string(),
        compressed_size,
        ratio: compressed_size as f64 / original_size as f64,
        compress_ms,
        decompress_ms,
        compress_mb_s: original_size as f64 / 1024.0 / 1024.0 / (compress_ms / 1000.0),
        decompress_mb_s: original_size as f64 / 1024.0 / 1024.0 / (decompress_ms / 1000.0),
        memory_bytes: end_stats.0.max(start_stats.0),
        cpu_percent: end_stats.1,
    })
}

fn write_csv_report(path: &Path, file_results: &[FileBenchmark]) -> io::Result<()> {
    let mut writer = Writer::from_path(path)?;
    writer.write_record(&[
        "file",
        "algorithm",
        "original_size",
        "compressed_size",
        "ratio",
        "compress_ms",
        "decompress_ms",
        "compress_mb_s",
        "decompress_mb_s",
        "memory_bytes",
        "cpu_percent",
    ])?;
    for file in file_results {
        for result in &file.algorithm_results {
            writer.serialize((
                &file.file_name,
                &result.algorithm,
                file.original_size,
                result.compressed_size,
                result.ratio,
                result.compress_ms,
                result.decompress_ms,
                result.compress_mb_s,
                result.decompress_mb_s,
                result.memory_bytes,
                result.cpu_percent,
            ))?;
        }
    }
    writer.flush()?;
    Ok(())
}

fn write_markdown_report(path: &Path, file_results: &[FileBenchmark]) -> io::Result<()> {
    let mut output = String::new();
    output.push_str("# NovaGraph Benchmark Summary\n\n");
    for file in file_results {
        output.push_str(&format!("## {}\n\n", file.file_name));
        output.push_str(&format!("- Original size: {} bytes\n", file.original_size));
        output.push_str(&format!("- NovaGraph compressed size: {} bytes\n", file.nova_report.total_compressed_bytes));
        output.push_str(&format!("- Compression ratio: {:.3}\n", file.nova_report.compression_ratio));
        output.push_str(&format!("- Blocks: {}\n", file.nova_report.blocks));
        output.push_str("\n### Algorithm comparisons\n\n");
        output.push_str("| Algorithm | Ratio | Compress MB/s | Decompress MB/s |\n");
        output.push_str("|---|---|---|---|\n");
        for result in &file.algorithm_results {
            output.push_str(&format!("| {} | {:.3} | {:.2} | {:.2} |\n", result.algorithm, result.ratio, result.compress_mb_s, result.decompress_mb_s));
        }
        output.push_str("\n");
        output.push_str("### NovaGraph stage timings\n\n");
        output.push_str("| Stage | Milliseconds |\n");
        output.push_str("|---|---|\n");
        for stage in &file.nova_report.stage_timings {
            output.push_str(&format!("| {} | {:.2} |\n", stage.stage, stage.duration_ms));
        }
        output.push_str("\n");
    }
    fs::write(path, output)
}

pub fn run_benchmark() -> io::Result<()> {
    let base = PathBuf::from("bench_data");
    let output_dir = PathBuf::from("bench_output");
    fs::create_dir_all(&output_dir)?;

    let files = make_sample_files(&base)?;
    let mut file_results = Vec::new();

    for file in files {
        let data = fs::read(&file)?;
        let original_size = data.len() as u64;

        let nova_path = output_dir.join(format!("{}.nova", file.file_name().unwrap().to_string_lossy()));
        let restored_path = output_dir.join(format!("{}.restored", file.file_name().unwrap().to_string_lossy()));

        let compressor = NovaCompressor::new_graph(1024 * 1024);
        let report = compressor.compress_file_with_report(&file, &nova_path)?;

        let decompressor = NovaDecompressor::new();
        let decomp_report = decompressor.decompress_file_with_report(&nova_path, &restored_path)?;

        let algorithm_results = vec![
            measure_algorithm("zlib", &data, compress_zlib, decompress_zlib)?,
            measure_algorithm("gzip", &data, compress_gzip, decompress_gzip)?,
            measure_algorithm("brotli", &data, compress_brotli, decompress_brotli)?,
            measure_algorithm("zstd", &data, compress_zstd, decompress_zstd)?,
        ];

        file_results.push(FileBenchmark {
            file_name: file.file_name().unwrap().to_string_lossy().to_string(),
            original_size,
            nova_report: report,
            nova_decompression: decomp_report,
            algorithm_results,
        });
    }

    let json_path = output_dir.join("benchmark.json");
    let csv_path = output_dir.join("benchmark.csv");
    let md_path = output_dir.join("benchmark.md");
    let json_file = File::create(&json_path)?;
    serde_json::to_writer_pretty(json_file, &file_results)?;
    write_csv_report(&csv_path, &file_results)?;
    write_markdown_report(&md_path, &file_results)?;

    println!("Benchmark complete. Reports written to {}", output_dir.display());
    Ok(())
}
