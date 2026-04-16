import csv
import os
import re
import time
import math
import subprocess
from datetime import datetime, timedelta
from urllib import request, error

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# =========================
# 配置区
# =========================
CHECK_INTERVAL = 60                  # 每60秒检测一次
MAX_RUNTIME_SECONDS = 2 * 60 * 60    # 最多运行2小时
DISPLAY_WINDOW_MINUTES = 30          # 图上只显示最近30分钟
OUTPUT_CSV = "latency_log.csv"
THRESHOLD_MS = 500

PING_IP = "1.1.1.1"

URLS = [
    "http://1.1.1.1",
    "https://www.youtube.com",
    "https://cp.cloudflare.com/generate_204",
]

SERIES_CONFIG = {
    "ICMP 1.1.1.1": {
        "target": PING_IP,
        "check_type": "ICMP_PING",
        "title": "ICMP Ping: 1.1.1.1",
    },
    "HTTP http://1.1.1.1": {
        "target": "http://1.1.1.1",
        "check_type": "HTTP_REQUEST",
        "title": "HTTP Latency: http://1.1.1.1",
    },
    "HTTPS youtube": {
        "target": "https://www.youtube.com",
        "check_type": "HTTP_REQUEST",
        "title": "HTTPS Latency: https://www.youtube.com",
    },
    "HTTPS cloudflare_204": {
        "target": "https://cp.cloudflare.com/generate_204",
        "check_type": "HTTP_REQUEST",
        "title": "HTTPS Latency: https://cp.cloudflare.com/generate_204",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


# =========================
# CSV日志
# =========================
def ensure_csv_header():
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "target",
                "check_type",
                "latency_ms",
                "status",
                "error",
            ])


def log_result(timestamp, target, check_type, latency_ms, status, err_msg=""):
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            target,
            check_type,
            "" if latency_ms is None else latency_ms,
            status,
            err_msg,
        ])


# =========================
# 网络测试
# =========================
def http_latency(url, timeout=15):
    req = request.Request(url, headers=HEADERS, method="GET")
    start = time.perf_counter()

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return elapsed_ms, f"HTTP {resp.status}", ""
    except error.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return elapsed_ms, f"HTTP {e.code}", str(e)
    except Exception as e:
        return None, "FAIL", str(e)


def ping_latency_windows(ip, timeout_ms=4000):
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
        )

        output = (result.stdout or "") + "\n" + (result.stderr or "")

        match = re.search(r"(?:time|时间)[=<]?\s*(\d+)\s*ms", output, re.IGNORECASE)
        if match:
            latency_ms = float(match.group(1))
            return latency_ms, "PING OK", ""

        if result.returncode == 0:
            return None, "PING UNKNOWN", "Ping succeeded but latency not parsed"
        return None, "PING FAIL", output.strip()

    except Exception as e:
        return None, "PING FAIL", str(e)


# =========================
# 绘图
# =========================
def init_plots():
    plt.ion()
    figures = {}
    axes = {}

    for series_name, cfg in SERIES_CONFIG.items():
        fig, ax = plt.subplots(figsize=(12, 5))
        fig.canvas.manager.set_window_title(series_name)
        figures[series_name] = fig
        axes[series_name] = ax

    return figures, axes


def get_recent_window(time_points, values, window_minutes):
    if not time_points:
        return [], []

    cutoff = time_points[-1] - timedelta(minutes=window_minutes)
    idxs = [i for i, t in enumerate(time_points) if t >= cutoff]

    recent_times = [time_points[i] for i in idxs]
    recent_values = [values[i] for i in idxs]
    return recent_times, recent_values


def update_single_plot(ax, series_name, time_points, values, elapsed_seconds):
    ax.clear()

    recent_times, recent_values = get_recent_window(
        time_points, values, DISPLAY_WINDOW_MINUTES
    )

    ax.plot(recent_times, recent_values, marker="o", linewidth=1.5, markersize=4)

    for x, val in zip(recent_times, recent_values):
        if val is not None and not math.isnan(val) and val > THRESHOLD_MS:
            ax.scatter([x], [val], s=60, marker="x", color="red", zorder=5)
            ax.annotate(
                f"{int(val)} ms",
                (x, val),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
                color="red",
            )

    ax.axhline(THRESHOLD_MS, linestyle="--", linewidth=1)

    remaining_seconds = max(0, MAX_RUNTIME_SECONDS - int(elapsed_seconds))
    used_minutes = int(elapsed_seconds) // 60
    remaining_minutes = remaining_seconds // 60

    ax.set_title(
        f"{SERIES_CONFIG[series_name]['title']} | "
        f"Elapsed: {used_minutes} min | Remaining: {remaining_minutes} min"
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Latency (ms)")
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    valid_values = [v for v in recent_values if v is not None and not math.isnan(v)]
    if valid_values:
        ymax = max(valid_values + [THRESHOLD_MS])
        ax.set_ylim(0, max(100, ymax * 1.2))
    else:
        ax.set_ylim(0, 100)

    plt.tight_layout()


def update_all_plots(figures, axes, time_points, series_data, elapsed_seconds):
    for series_name in SERIES_CONFIG.keys():
        if plt.fignum_exists(figures[series_name].number):
            update_single_plot(
                axes[series_name],
                series_name,
                time_points,
                series_data[series_name],
                elapsed_seconds,
            )

    plt.pause(0.1)


def all_windows_closed(figures):
    return all(not plt.fignum_exists(fig.number) for fig in figures.values())


# =========================
# 主程序
# =========================
def main():
    ensure_csv_header()

    time_points = []
    series_data = {name: [] for name in SERIES_CONFIG.keys()}

    figures, axes = init_plots()
    start_time = time.time()
    max_rounds = MAX_RUNTIME_SECONDS // CHECK_INTERVAL

    print("开始实时监控。")
    print(f"检测间隔: {CHECK_INTERVAL} 秒")
    print(f"最长运行: {MAX_RUNTIME_SECONDS // 60} 分钟")
    print(f"图上仅显示最近: {DISPLAY_WINDOW_MINUTES} 分钟")
    print(f"超过 {THRESHOLD_MS} ms 的点会标红标注")
    print(f"日志文件: {OUTPUT_CSV}")
    print(f"预计最多检测 {max_rounds} 次")
    print("关闭全部图窗或按 Ctrl + C 可提前结束。")

    try:
        round_num = 0
        while True:
            elapsed_seconds = time.time() - start_time
            if elapsed_seconds >= MAX_RUNTIME_SECONDS:
                print("\n已达到最长运行时间 2 小时，程序自动结束。")
                break

            if all_windows_closed(figures):
                print("所有图窗已关闭，程序结束。")
                break

            round_num += 1
            now_dt = datetime.now()
            timestamp = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            time_points.append(now_dt)

            print(f"\n========== 第 {round_num}/{max_rounds} 次检测 [{timestamp}] ==========")

            # 1. ICMP ping
            ping_ms, ping_status, ping_err = ping_latency_windows(PING_IP)
            log_result(timestamp, PING_IP, "ICMP_PING", ping_ms, ping_status, ping_err)
            series_data["ICMP 1.1.1.1"].append(float("nan") if ping_ms is None else ping_ms)
            print(f"[PING ] {PING_IP:<35} -> {ping_ms} ms | {ping_status}")

            # 2. HTTP/HTTPS
            http_targets = [
                ("HTTP http://1.1.1.1", "http://1.1.1.1"),
                ("HTTPS youtube", "https://www.youtube.com"),
                ("HTTPS cloudflare_204", "https://cp.cloudflare.com/generate_204"),
            ]

            for series_name, url in http_targets:
                ms, status, err_msg = http_latency(url)
                log_result(timestamp, url, "HTTP_REQUEST", ms, status, err_msg)
                series_data[series_name].append(float("nan") if ms is None else ms)
                print(f"[HTTP ] {url:<35} -> {ms} ms | {status}")

            update_all_plots(figures, axes, time_points, series_data, elapsed_seconds)

            remaining = MAX_RUNTIME_SECONDS - (time.time() - start_time)
            if remaining <= 0:
                print("\n已达到最长运行时间 2 小时，程序自动结束。")
                break

            time.sleep(min(CHECK_INTERVAL, remaining))

    except KeyboardInterrupt:
        print("\n用户手动中断，程序结束。")
    finally:
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()