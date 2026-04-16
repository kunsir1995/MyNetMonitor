# MyNetMonitor

A simple Python-based network latency monitor for Windows.

## Features

- Tests latency every 60 seconds
- Monitors these targets:
  - ICMP ping to `1.1.1.1`
  - `http://1.1.1.1`
  - `https://www.youtube.com`
  - `https://cp.cloudflare.com/generate_204`
- Draws real-time latency plots
- Highlights points above `500 ms`
- Shows only the most recent `30 minutes` in the plots
- Stops automatically after `2 hours`
- Saves all results to `latency_log.csv`

## Requirements

- Windows 10 / 11
- Python 3.12 recommended
- `matplotlib`

## Install

Use conda or pip.

### Conda
```bash
conda install matplotlib

### Pip

```bash
pip install matplotlib


## Usage

Open a terminal in the project folder and run:

```bash
python latency_monitor_plot.py
```

## Output

The program will:

- open real-time plot windows for each monitored target
- save measurement results to `latency_log.csv`

The CSV file includes:

- timestamp
- target
- check type
- latency in milliseconds
- status code or ping status
- error message if a request fails

## Monitored Targets

### 1. ICMP Ping
- `1.1.1.1`

This measures traditional ping latency using the Windows `ping` command.

### 2. HTTP/HTTPS Requests
- `http://1.1.1.1`
- `https://www.youtube.com`
- `https://cp.cloudflare.com/generate_204`

These measure application-layer request latency rather than raw ICMP latency.

## Notes

- ICMP ping and HTTP/HTTPS request latency are not the same thing
- YouTube latency may be much higher and more variable than the other targets
- Failed requests are recorded in the CSV log
- Values above `500 ms` are marked in the plots

## Project Structure

```text
MyNetMonitor/
├─ latency_monitor_plot.py
├─ README.md
├─ LICENSE
└─ .gitignore
```

## Possible Improvements

Future improvements may include:

- automatic summary statistics after monitoring ends
- optional alerting for repeated failures or high latency
- support for custom targets from a config file
- exporting a final summary figure automatically

## License

This project is licensed under the MIT License.