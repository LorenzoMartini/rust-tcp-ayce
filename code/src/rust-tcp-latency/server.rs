extern crate bytes;
extern crate rust_tcp_io_perf;
extern crate streaming_harness_hdrhist;

use rust_tcp_io_perf::config;
use rust_tcp_io_perf::connection;
use rust_tcp_io_perf::threading;

fn main() {

    let args = config::parse_config();
    let n_bytes = args.n_bytes;
    let n_rounds = args.n_rounds;
    let mut buf = vec![0; n_bytes];

    let mut stream = connection::server_listen_and_get_first_connection(&args.port);
    connection::setup(&args, &mut stream);
    threading::setup(&args);

    let mut hist_send = streaming_harness_hdrhist::HDRHist::new();
    let mut hist_recv = streaming_harness_hdrhist::HDRHist::new();
    // Make sure n_rounds is the same between client and server
    for _i in 0..n_rounds {
        hist_recv.add_value(connection::receive_message(n_bytes, &mut stream, &mut buf));
        hist_send.add_value(connection::send_message(n_bytes, &mut stream, &buf));
    }

    println!("Done exchanging stuff");
    println!("Send\n{}", hist_send.summary_string());
    println!("Recv\n{}", hist_recv.summary_string());
}
