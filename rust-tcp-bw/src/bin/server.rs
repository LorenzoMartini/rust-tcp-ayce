extern crate bytes;
extern crate rust_tcp_bw;
extern crate streaming_harness_hdrhist;

use std::time::Instant;
use std::net::TcpListener;
use std::io::Read;
use rust_tcp_bw::config;

struct Measure {
    start: Instant,
    end: Instant,
    n_bytes: usize,
}

fn print_line() {
    println!("\n-------------------------------------------------------------\n");
}

fn main() {
    let args = config::parse_config();
    let n_bytes = args.n_kbytes * 1000;

    let mut buf = vec![0; n_bytes];
    let mut active = true;
    let mut measurements = Vec::new();

    let listener = TcpListener::bind("0.0.0.0:".to_owned() + &args.port).unwrap();

    println!("Server running, listening for connection on 0.0.0.0:{}", &args.port);

    let mut stream = listener.incoming().next().unwrap().unwrap();

    println!("Connection established with {:?}!\nExpected {} Bytes for {} rounds",
             stream.peer_addr().unwrap(), n_bytes, args.n_rounds);

    let mut start = Instant::now();
    while active {
        let recv = stream.read(&mut buf).unwrap();
        if recv > 0 {
            let end = Instant::now();
            measurements.push(Measure {
                start,
                end,
                n_bytes: recv,
            });
            start = end;
        } else {
            active = false;
        }
    }

    println!("Done reading, Computing summary...");

    let mut tot_bytes: u64 = 0;
    let mut tot_time: u64 = 0;
    let len = measurements.len();
    let mut hist = streaming_harness_hdrhist::HDRHist::new();
    for i in 0..len {
        let entry = &measurements[i];
        let duration = entry.end.duration_since(entry.start);
        let duration_us = duration.as_secs() * 1_000_000u64 + duration.subsec_micros() as u64;
        let duration_ns = duration.as_secs() * 1_000_000_000u64 + duration.subsec_nanos() as u64;

        // Add measurement to compute bw
        if i > len / 3 && i < (len * 2 / 3) {
            tot_bytes += entry.n_bytes as u64;
            tot_time += duration_us;
        }
        hist.add_value(duration_ns);
    }

    // Format output nicely
    print_line();
    println!("HDRHIST summary, measure in ns");
    print_line();
    println!("summary:\n{:#?}", hist.summary().collect::<Vec<_>>());
    print_line();
    println!("Summary_string:\n{}", hist.summary_string());
    print_line();
    println!("CDF summary:\n");
    for entry in hist.ccdf() {
        println!("{:?}", entry);
    }
    print_line();
    println!("Available approximated bandwidth: {} MB/s", tot_bytes / tot_time);
    print_line();
}
