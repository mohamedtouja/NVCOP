use novagraph_rust::benchmark::run_benchmark;

fn main() {
    if let Err(err) = run_benchmark() {
        eprintln!("Benchmark failed: {}", err);
        std::process::exit(1);
    }
}
