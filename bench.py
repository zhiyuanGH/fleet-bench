import os
import time
import csv
import re
import requests
import subprocess
import argparse

# Global variables
latency_set = [0, 50, 100, 150, 200, 250, 300, 350, 400]
# List of different latency values to be tested in milliseconds

bandwidth_set = [500]
# List of bandwidth values to be tested in Mbps

containers_extend = [
    "ubuntu", "tensorflow", "nginx", "httpd", "node", "tomcat",
    "postgres", "redis", "mysql", "rabbitmq", "py", "golang",
    "ghost", "wordpress", "alpine", "pytorch", "gcc", "kafka",
    "mariadb", "openjdk",
]
# List of container images to be tested

ready_messages = {
    "httpd": "Apache/2.4.57 (Unix) configured -- resuming normal operations",
    "tensorflow": "Skipped non-installed server(s)",
    "nginx": "start worker process",
    "tomcat": "org.apache.catalina.startup.Catalina.start Server startup",
    "redis": "Ready to accept connections",
    "rabbitmq": "Server startup complete; 3 plugins started.",
    "wordpress": "Complete! WordPress has been successfully copied to /var/www/html",
}
# Dictionary mapping container names to their ready messages

result_file_template = "provisioning_times_{snapshotter}_fleetbench.csv"
# Template for the result file name

metrics_file_template = "metrics_sum_{snapshotter}_fleetbench.csv"
# Template for the metrics file name

iterations = 5
# Number of iterations to run for each container

delay = 2
# Delay in seconds between certain operations

rtt = "0ms"
# Default round-trip time (RTT) for network conditions

Bandwidth = "0Mbps"
# Default bandwidth for network conditions

metrics_pattern_estargz = re.compile(
    r'stargz_fs_operation_count{.*operation_type="on_demand_remote_registry_fetch_count"} (\d+)'
)
# Regex pattern to extract estargz metrics

metrics_pattern_fleet = re.compile(
    r'fleet_fs_operation_count{.*operation_type="on_demand_remote_registry_fetch_count"} (\d+)'
)
# Regex pattern to extract fleet metrics

def create_results_files(snapshotter):
    """
    Create result and metrics files if they don't exist.
    
    Args:
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
    """
    result_file = result_file_template.format(snapshotter=snapshotter)
    metrics_file = metrics_file_template.format(snapshotter=snapshotter)

    if not os.path.isfile(result_file):
        with open(result_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Container", "Iteration", "Time", "RTT", "Bandwidth"])

    if not os.path.isfile(metrics_file):
        with open(metrics_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Container", "Iteration", "Metrics Sum", "RTT", "Bandwidth"]
            )

def reset_snapshotter(snapshotter, delay=delay):
    """
    Reset the snapshotter by stopping all containers, pruning images,
    and restarting the snapshotter service.
    
    Args:
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
        delay (int): Delay in seconds between operations.
    """
    print(f"Resetting {snapshotter} snapshotter...")
    time.sleep(delay)
    # Stop all containers
    subprocess.run("nerdctl stop $(nerdctl ps -q)", shell=True)
    time.sleep(1)
    subprocess.run("nerdctl rm $(nerdctl ps -a -q)", shell=True)
    time.sleep(1)
    subprocess.run(["nerdctl", "image", "prune", "-af"], check=True)
    time.sleep(1)

    if snapshotter in ["stargz", "fleet"]:
        subprocess.run(["sudo", "systemctl", "restart", f"{snapshotter}-snapshotter"], check=True)
        time.sleep(1)
        subprocess.run(["sudo", "systemctl", "stop", f"{snapshotter}-snapshotter"], check=True)
        time.sleep(1)
        subprocess.run(
            f"sudo rm -rf /var/lib/containerd-{snapshotter}-grpc/*",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        time.sleep(1)
        subprocess.run(["sudo", "systemctl", "restart", f"{snapshotter}-snapshotter"], check=True)

    elif snapshotter == "overlayfs":
        subprocess.run(
            "sudo rm -rf /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/*",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        time.sleep(1)
        subprocess.run(["sudo", "systemctl", "restart", "containerd"], check=True)

    time.sleep(1)
    print("Reset complete.")

def run_container(container, snapshotter, delay=delay):
    """
    Run the specified container using the specified snapshotter and measure the time taken.
    
    Args:
        container (str): The container image to run.
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
        delay (int): Delay in seconds between operations.
    
    Returns:
        str: The formatted time taken to run the container.
    """
    formatted_time = "90s (timeout) init"
    print(f"Running container {container}...")
    image = f"{container}:{snapshotter[:3]}"

    command = [
        "nerdctl",
        "run",
        "--rm",
        "--insecure-registry",
        f"--snapshotter={snapshotter}",
        f"158.132.255.111:5000/{image}",
    ]

    start_time = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    if container in ready_messages:
        print(f"Long-term container. Monitoring the ready message: {ready_messages[container]}")
        for line in iter(process.stdout.readline, ""):
            print(line)
            if ready_messages[container] in line:
                elapsed_time = time.perf_counter() - start_time
                minutes, seconds = divmod(elapsed_time, 60)
                formatted_time = f"{int(minutes)}m{seconds:.3f}s"
                print("break: " + line)
                print(f"terminating container: {container}")
                process.kill()
                print(f"send terminating container: {container}")
                process.wait()
                print(f"complete terminating container: {container}")
                break
    else:
        try:
            print("Short-term container.")
            for line in iter(process.stdout.readline, ""):
                print(line)
            process.wait(timeout=900)  # Set timeout to 90 seconds, for example
            elapsed_time = time.perf_counter() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            formatted_time = f"{int(minutes)}m{seconds:.3f}s"
        except subprocess.TimeoutExpired:
            print("Process took too long to complete. Terminating...")
            process.kill()
            formatted_time = "90s (timeout)"

    process.terminate()  # Stop the container
    process.wait()
    print(f"Container run complete in {formatted_time}.")

    return formatted_time

def record_results(container, i, formatted_time, snapshotter, RTT=rtt, Bandwidth=Bandwidth):
    """
    Record the results of running the container to a CSV file.
    
    Args:
        container (str): The container image that was run.
        i (int): The iteration number.
        formatted_time (str): The time taken to run the container.
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
        RTT (str): The round-trip time in milliseconds.
        Bandwidth (str): The bandwidth in Mbps.
    """
    result_file = result_file_template.format(snapshotter=snapshotter)
    with open(result_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [container, i + 1, formatted_time, str(RTT) + "ms", str(Bandwidth) + "Mbps"]
        )
    print(f"Recorded time for iteration {i+1}: {formatted_time}")

def capture_metrics(snapshotter):
    """
    Capture the metrics from the snapshotter's metrics endpoint.
    
    Args:
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
    
    Returns:
        int: The sum of the metrics captured.
    """
    if snapshotter == "stargz":
        print("Capturing metrics...")
        response = requests.get("http://127.0.0.1:8234/metrics")
        metrics_matches = metrics_pattern_estargz.findall(response.text)
    elif snapshotter == "fleet":
        print("Capturing metrics...")
        response = requests.get("http://127.0.0.1:8334/metrics")
        metrics_matches = metrics_pattern_fleet.findall(response.text)
    else:
        return None  # No metrics for overlayfs

    metrics_sum = sum(int(m) for m in metrics_matches)
    return metrics_sum

def record_metrics(container, i, metrics_sum, snapshotter, RTT=rtt, Bandwidth=Bandwidth):
    """
    Record the metrics sum to a CSV file.
    
    Args:
        container (str): The container image that was run.
        i (int): The iteration number.
        metrics_sum (int): The sum of the metrics captured.
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
        RTT (str): The round-trip time in milliseconds.
        Bandwidth (str): The bandwidth in Mbps.
    """
    metrics_file = metrics_file_template.format(snapshotter=snapshotter)
    with open(metrics_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [container, i + 1, metrics_sum, str(RTT) + "ms", str(Bandwidth) + "Mbps"]
        )
    print(f"Recorded metrics sum for iteration {i+1}: {metrics_sum}")

def set_network_conditions(bandwidth, latency, server_ip="158.132.255.111"):
    """
    Set network conditions on the server using ssh and bash script.
    
    Args:
        bandwidth (int): The bandwidth in Mbps.
        latency (int): The latency in milliseconds.
        server_ip (str): The IP address of the server.
    
    Returns:
        tuple: The stdout and stderr from the command.
    """
    password = "gh"
    command = f'sshpass -p {password} ssh root@{server_ip} "bash /home/gh/code/lab/nw.sh {bandwidth}mbit {latency}ms"'
    print(command)
    completed_process = subprocess.run(
        command, shell=True, capture_output=True, text=True
    )
    print(f"Successfully set network conditions on server {server_ip}.")
    print(f"Output: {completed_process.stdout}")
    print(f"Errors: {completed_process.stderr}")
    return completed_process.stdout, completed_process.stderr

def main(containers=containers_extend, iterations=iterations, snapshotter="overlayfs"):
    """
    Main function to run container performance tests with specified snapshotter.
    
    Args:
        containers (list): List of container images to be tested.
        iterations (int): Number of iterations to run for each container.
        snapshotter (str): The snapshotter type (overlayfs, stargz, fleet).
    """
    create_results_files(snapshotter)

    for bw in bandwidth_set:
        for latency in latency_set:
            _, error = set_network_conditions(bw, latency)
            if error:  
                print(
                    f"Error setting network conditions: {error}. Skipping experiments for {bw}bandwidth and {latency}latency."
                )
                continue  

            for container in containers:
                print(
                    f"Starting tests for container: {container} under {bw}bandwidth and {latency}latency\n"
                )
                for i in range(iterations):
                    print(
                        f"Starting iteration {i+1} for container: {container} under {bw}bandwidth and {latency}latency\n"
                    )

                    reset_snapshotter(snapshotter)

                    time_taken = run_container(container, snapshotter)
                    record_results(container, i, time_taken, snapshotter, RTT=latency, Bandwidth=bw)
                    metrics_sum = capture_metrics(snapshotter)
                    if metrics_sum is not None:
                        record_metrics(
                            container, i, metrics_sum, snapshotter, RTT=latency, Bandwidth=bw
                        )
                print(
                    f"All tests for container {container} under {bw}bandwidth and {latency}latency completed.\n"
                )

    print("All experiments completed.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run container performance tests with specified snapshotter.")
    parser.add_argument('snapshotter', type=str, choices=['overlayfs', 'stargz', 'fleet'],
                        help="The snapshotter to use: overlayfs, stargz, or fleet.")
    args = parser.parse_args()
    main(snapshotter=args.snapshotter)
