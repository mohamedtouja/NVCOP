use std::env;
use std::path::PathBuf;

use novagraph_rust::{NovaCompressor, NovaDecompressor};

fn print_usage() {
    eprintln!("NovaGraph Rust Compressor v0.1.0");
    eprintln!("Usage:");
    eprintln!("  novagraph-rust compress <input> <output>");
    eprintln!("  novagraph-rust decompress <input> <output>");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 4 {
        print_usage();
        std::process::exit(1);
    }

    let command = args[1].as_str();
    let input = PathBuf::from(&args[2]);
    let output = PathBuf::from(&args[3]);

    match command {
        "compress" => {
            let compressor = NovaCompressor::new(1024 * 1024);
            compressor.compress_file(&input, &output).unwrap();
            println!("Compressed {} -> {}", input.display(), output.display());
        }
        "decompress" => {
            let decompressor = NovaDecompressor::new();
            decompressor.decompress_file(&input, &output).unwrap();
            println!("Decompressed {} -> {}", input.display(), output.display());
        }
        _ => {
            print_usage();
            std::process::exit(1);
        }
    }
}
