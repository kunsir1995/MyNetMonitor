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