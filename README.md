# Container Performance Benchmarking with Different Snapshotters

Welcome to the Container Performance Benchmarking project! This repository contains scripts to run containers using different snapshotters and measure their performance, including provisioning time and a specific metric. Additionally, it includes a script to visualize the performance results for easier analysis.

### Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
  - [Running the Benchmark](#running-the-benchmark)
  - [Visualizing the Results](#visualizing-the-results)
- [Results](#results)
- [Contributing](#contributing)
- [License](#license)

## Introduction

In containerized environments, the choice of snapshotter can significantly impact performance. This project aims to provide insights into the performance of various snapshotters such as `overlayfs`, `stargz`, and `fleet`. By running containers with different snapshotters and measuring key performance metrics, users can make informed decisions on the best snapshotter for their needs.

## Features

- **Performance Benchmarking**: Measure provisioning time and specific metrics for containers using different snapshotters.
- **Network Conditions Simulation**: Test containers under various network conditions by setting bandwidth and latency.
- **Visualization**: Generate detailed plots to compare the performance of different snapshotters.

## Prerequisites

Before using this project, ensure you have the following installed:

- Nerdctl and containerd
- SSH access to the server with appropriate permissions

## Usage

### Running the Benchmark

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zhiyuanGH/fleet-bench.git
   cd container-performance-benchmarking
   ```

2. **Install the required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the benchmarking script**:
   ```bash
   python3 bench.py overlayfs
   ```
   Replace `overlayfs` with `stargz` or `fleet` to use different snapshotters.

### Visualizing the Results

1. **Ensure the benchmark results are available**:
   The benchmarking script generates CSV files with provisioning times and metrics in the current directory.

2. **Run the visualization script**:
   ```bash
   python3 draw_selected_cases.py
   ```

3. **View the generated plots**:
   The script will generate and display plots comparing the performance of different snapshotters. The plots will also be saved as files.

## Results

The results are presented in the form of CSV files and visual plots:

- **CSV Files**: Contain detailed provisioning times and metrics for each container.
- **Plots**: Provide a visual comparison of provisioning times, on-demand fetch metrics, and acceleration rates for different snapshotters.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. For major changes, please discuss them in an issue first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Happy benchmarking! If you have any questions or need further assistance, feel free to reach out.

