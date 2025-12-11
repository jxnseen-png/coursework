import socket
import time
import threading
import argparse
import sys
from typing import Optional
import csv
from typing import List
import select
import struct

# -----------------------------------------------------------------------------
# PROFESSOR'S CODE (DO NOT CHANGE)
# -----------------------------------------------------------------------------


class Logger:
    """
    Logger
    ------
    Logger class for recording and displaying network test metrics"""

    INFO = '\033[94m[INFO]\033[0m '
    ERROR = '\033[91m[ERROR]\033[0m '

    class Stat:
        """A class to model a single measurement record"""

        def __init__(self, timestamp: float, bandwidth: Optional[float] = None,
                     loss: Optional[float] = None, jitter: Optional[float] = None):
            self.timestamp = timestamp
            self.bandwidth = bandwidth
            self.loss = loss
            self.jitter = jitter

    def __init__(self, csv_output: Optional[str] = "results.csv"):
        """Initialize Logger with optional CSV output"""
        self.stats: List[Logger.Stat] = []  # List to store measurements
        self.csv_output = csv_output        # CSV file path or None
        self.csv_file = None               # File handle for CSV
        self.csv_writer = None             # CSV writer object

        # If the csv parameter is None, then disable CSV output
        if csv_output:
            self.csv_file = open(csv_output, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(
                ['timestamp', 'elapsed', 'bandwidth_mbps', 'loss_percent', 'jitter_ms'])

    def log_stat(self, timestamp: float, ip: str, port: int, bandwidth: Optional[float] = None,
                 loss: Optional[float] = None, jitter: Optional[float] = None) -> None:
        """Log a measurement"""
        stat = Logger.Stat(timestamp, bandwidth, loss, jitter)
        self.stats.append(stat)
        elapsed = 0.0
        if len(self.stats) > 1:
            elapsed = timestamp - self.stats[0].timestamp

        # Write to CSV if enabled
        if self.csv_writer:
            self.csv_writer.writerow([
                ip, port,
                timestamp,
                f"{elapsed:.3f}",
                f"{bandwidth:.2f}" if bandwidth is not None else "",
                f"{loss:.2f}" if loss is not None else "",
                f"{jitter:.2f}" if jitter is not None else ""
            ])
            self.csv_file.flush()

        parts = [f"[{int(elapsed):03d}s] [Client:{ip}:{port}]"]

        if bandwidth is not None:
            parts.append(f"Bandwidth: {bandwidth:.2f} Mbps")
        if loss is not None:
            parts.append(f"Loss: {loss:.2f}%")
        if jitter is not None:
            parts.append(f"Jitter: {jitter:.6f} ms")

        print(" ".join(parts))

    def summary(self) -> None:
        """Print summary statistics"""
        if not self.stats:
            print(f"{Logger.INFO}No statistics recorded")
            return

        print(f"\n{Logger.INFO}=== Test Summary ===")
        print(
            f"  Duration: {int(self.stats[-1].timestamp - self.stats[0].timestamp)}s")
        print(f"  Measurements: {len(self.stats)}")

        # Calculate averages
        bw_values = [
            s.bandwidth for s in self.stats if s.bandwidth is not None]
        loss_values = [s.loss for s in self.stats if s.loss is not None]
        jitter_values = [s.jitter for s in self.stats if s.jitter is not None]

        if bw_values:
            print(f"  Bandwidth: avg={sum(bw_values)/len(bw_values):.2f} Mbps, "
                  f"min={min(bw_values):.2f}, max={max(bw_values):.2f}")
        if loss_values:
            print(f"  Loss: avg={sum(loss_values)/len(loss_values):.2f}%, "
                  f"min={min(loss_values):.2f}, max={max(loss_values):.2f}")
        if jitter_values:
            print(f"  Jitter: avg={sum(jitter_values)/len(jitter_values):.2f} ms, "
                  f"min={min(jitter_values):.2f}, max={max(jitter_values):.2f}")

        if self.csv_output:
            self.log_info(f"Results saved to {self.csv_output}")

    def close(self) -> None:
        """Close CSV file if open"""
        if self.csv_file:
            self.csv_file.close()

    def log_info(self, message: str) -> None:
        print(f"{Logger.INFO}{message}")

    def log_error(self, message: str) -> None:
        print(f"{Logger.ERROR}{message}")


# -----------------------------------------------------------------------------
# MY CODE STARTS HERE :)
# -----------------------------------------------------------------------------

# ---------------------- TCP Functions (Task 2) ----------------------

def tester_tcp_client(log: Logger, server_ip: str, server_port: int,
                      duration: int, interval: int) -> None:
    """TCP client (Task 2)"""
    log.log_info(f"Starting TCP client to {server_ip}:{server_port} "
                 f"for {duration}s")

    try:
        # creating the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, server_port))  # connect to server

        # simple chunk of data to send
        data_chunk = b'x' * 1000

        start_time = time.time()
        end_time = start_time + duration

        # keeping track of bytes
        bytes_sent = 0
        last_log_time = start_time

        while time.time() < end_time:
            # send the data
            sock.sendall(data_chunk)
            bytes_sent = bytes_sent + len(data_chunk)

            # check if we need to print stats
            current_time = time.time()
            if current_time - last_log_time >= interval:
                # calculate bandwidth
                time_elapsed = current_time - last_log_time
                bits = bytes_sent * 8
                mbps = (bits / time_elapsed) / \
                    1_000_000  # convert to mega bits

                log.log_stat(current_time, server_ip,
                             server_port, bandwidth=mbps)

                # reset for next loop
                bytes_sent = 0
                last_log_time = current_time

        sock.close()

    except Exception as e:
        log.log_error(f"Error in client: {e}")

    return None


def tester_tcp_server(log: Logger, port: int) -> None:
    """TCP server (Task 2)"""
    log.log_info(f"Starting TCP server on port {port}")

    # helper function for threads
    def single_client(client_socket, client_address):
        total_bytes = 0
        start_t = time.time()
        try:
            while True:
                # receive data
                data = client_socket.recv(1024)
                if not data:
                    break  # connection closed
                total_bytes = total_bytes + len(data)
        except Exception:
            pass
        finally:
            end_t = time.time()
            elapsed = end_t - start_t
            if elapsed > 0:
                # calculate bw on server side
                bw = (total_bytes * 8) / (elapsed * 1_000_000)
                log.log_stat(
                    end_t, client_address[0], client_address[1], bandwidth=bw)

            client_socket.close()

    try:
        # setup server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(5)

        while True:
            # wait for connections
            client_socket, client_address = server_socket.accept()
            # start thread for client
            client_handler = threading.Thread(
                target=single_client, args=(client_socket, client_address))
            client_handler.start()

    except KeyboardInterrupt:
        log.log_info("Stopping server...")
        server_socket.close()

    return None


# ---------------------- UDP Functions (Tasks 3 & 4) ----------------------

def tester_udp_client(log: Logger, server_ip: str, server_port: int, duration: int, interval: int,
                      rate_kbps: int, ack: bool) -> None:
    """UDP client"""
    log.log_info(f"Starting UDP client to {server_ip}:{server_port} "
                 f"for {duration}s at {rate_kbps} Kbps (ack={ack})")

    # setup udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)  # timeout for acks

    seq_num = 1
    padding = b'x' * 1012

    # figuring out sleep time based on rate
    bytes_per_second = (rate_kbps * 1000) / 8
    packet_size = 1016  # header(4) + padding(1012)
    packets_per_second = bytes_per_second / packet_size
    sleep_interval = 1.0 / packets_per_second

    start_time = time.time()

    # stats variables
    acked_bytes = 0
    total_jitters = 0
    ack_count = 0

    times_sent = {}
    previous_ack_rx = 0
    previous_ack_tx = 0

    last_log_time = start_time

    try:
        while time.time() < start_time + duration:
            now = time.time()

            # create packet with ID and time
            header = struct.pack('!Id', seq_num, now)
            packet = header + padding

            # send it
            sock.sendto(packet, (server_ip, server_port))

            if ack:
                times_sent[seq_num] = now

            seq_num = seq_num + 1

            # task 4: check for acks
            if ack:
                while True:
                    try:
                        data, _ = sock.recvfrom(1024)
                        rx_time = time.time()

                        if len(data) >= 4:
                            ack_id = struct.unpack('!I', data[:4])[0]

                            if ack_id in times_sent:
                                original_time = times_sent[ack_id]
                                ack_count = ack_count + 1
                                acked_bytes = acked_bytes + packet_size

                                # calc jitter
                                if ack_count > 1:
                                    diff_rx = rx_time - previous_ack_rx
                                    diff_tx = original_time - previous_ack_tx
                                    jitter = abs(diff_rx - diff_tx)
                                    total_jitters = total_jitters + jitter

                                previous_ack_rx = rx_time
                                previous_ack_tx = original_time
                    except socket.timeout:
                        break  # done with acks for now
                    except Exception:
                        break

            # logging
            if now - last_log_time >= interval:
                if ack:
                    bw = (acked_bytes * 8) / interval / 1_000_000

                    average_jitter = 0
                    if ack_count > 1:
                        average_jitter = (
                            total_jitters / (ack_count - 1)) * 1000

                    # estimating loss
                    loss = 0
                    if seq_num > 1:
                        loss = (1 - (ack_count / (seq_num - 1))) * 100

                    log.log_stat(now, server_ip, server_port,
                                 bandwidth=bw, jitter=average_jitter, loss=loss)

                    # reset stats
                    acked_bytes = 0
                    total_jitters = 0
                    ack_count = 0
                last_log_time = now

            time.sleep(sleep_interval)

    finally:
        # send end packet
        end_packet = struct.pack('!Id', 0, time.time())
        sock.sendto(end_packet, (server_ip, server_port))
        sock.close()

    return None


def tester_udp_server(log: Logger, port: int, rate: int, interval: int, ack: bool) -> None:
    """UDP server"""
    log.log_info(f"Starting UDP server on port {port} (ack={ack})")

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    clients = {}

    try:
        while True:
            # get data
            data, addr = s.recvfrom(2048)
            rx_time = time.time()

            if len(data) >= 12:
                seq_num, tx_time = struct.unpack('!Id', data[:12])

                if seq_num == 0:
                    continue  # client finished

                client_id = addr
                if client_id not in clients:
                    clients[client_id] = {
                        'count': 0, 'bytes': 0, 'max_seq': seq_num-1, 'lost': 0,
                        'jitter_sum': 0, 'last_rx': 0, 'last_tx': 0, 'start_time': rx_time
                    }

                client = clients[client_id]
                client['count'] = client['count'] + 1
                client['bytes'] = client['bytes'] + len(data)

                # check for packet loss
                if seq_num > client['max_seq']:
                    if seq_num > client['max_seq'] + 1:
                        client['lost'] = client['lost'] + \
                            (seq_num - client['max_seq'] - 1)
                    client['max_seq'] = seq_num

                # check jitter
                if client['count'] > 1:
                    diff_rx = rx_time - client['last_rx']
                    diff_tx = tx_time - client['last_tx']
                    jitter = abs(diff_rx - diff_tx)
                    client['jitter_sum'] = client['jitter_sum'] + jitter

                client['last_rx'] = rx_time
                client['last_tx'] = tx_time

                # check if we need to log
                if rx_time - client['start_time'] >= interval:
                    elapsed = rx_time - client['start_time']
                    bandwidth = (client['bytes'] * 8) / elapsed / 1_000_000

                    average_jitter = 0
                    if client['count'] > 1:
                        average_jitter = (
                            client['jitter_sum'] / (client['count'] - 1)) * 1000

                    loss = 0
                    if client['max_seq'] > 0:
                        expected = client['max_seq']
                        actual = client['count']
                        loss = ((expected - actual) / expected) * 100
                        if loss < 0:
                            loss = 0

                    log.log_stat(
                        rx_time, addr[0], addr[1], bandwidth=bandwidth, jitter=average_jitter, loss=loss)

                    # reset for next interval
                    client['bytes'] = 0
                    client['lost'] = 0
                    client['jitter_sum'] = 0
                    client['count'] = 0
                    client['start_time'] = rx_time

                # if ack is enabled send it back
                if ack:
                    ack_packet = struct.pack('!I', seq_num)
                    s.sendto(ack_packet, addr)

    except KeyboardInterrupt:
        log.log_info("Shutting down UDP server...")
    finally:
        s.close()

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SCC.231 net-tester application")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-s", "--server", action="store_true",
                      help="Run in server mode")
    mode.add_argument("-c", "--client", metavar="ADDR",
                      help="Run in client mode, connect to ADDR")

    parser.add_argument("-p", "--port", type=int,
                        default=5001, help="Port (default 5001)")
    parser.add_argument("-u", "--udp", action="store_true",
                        help="Use UDP (default TCP)")
    parser.add_argument("-a", "--ack", action="store_true",
                        help="(UDP) Enable acknowledgements")
    parser.add_argument("-t", "--duration", type=int,
                        default=60, help="Test duration seconds (default 60)")
    parser.add_argument("-i", "--interval", type=int, default=1,
                        help="Report interval seconds (default 1)")
    parser.add_argument("-r", "--rate", type=int, default=1000,
                        help="(UDP) send rate Kbps (default 1000)")
    parser.add_argument('-l', '--log', type=str, default=None,
                        help='Path to CSV log file (default: None)')

    args = parser.parse_args()
    log = Logger(csv_output=args.log)

    if args.server:
        if args.udp:
            tester_udp_server(log, args.port, args.rate,
                              args.interval, args.ack)
        else:
            tester_tcp_server(log, args.port)
    else:
        if args.udp:
            tester_udp_client(log, args.client, args.port,
                              args.duration, args.interval,
                              args.rate, args.ack)
        else:
            tester_tcp_client(log, args.client, args.port,
                              args.duration, args.interval)
    log.summary()
    log.close()
