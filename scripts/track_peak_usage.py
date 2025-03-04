#!/usr/bin/env python3

"""
Peak CPU and RAM Usage Tracker

This script monitors and tracks the peak CPU and RAM usage over a specified period.
It records the highest values observed and provides a summary at the end.
"""

import os
import sys
import time
import logging
import argparse
import datetime
import psutil
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/peak_usage.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('peak_monitor')

# Create monitoring directory if it doesn't exist
Path("monitoring").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

def get_current_usage():
    """Get current CPU and memory usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used_gb = memory.used / (1024 ** 3)
    memory_total_gb = memory.total / (1024 ** 3)
    
    return {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'memory_used_gb': memory_used_gb,
        'memory_total_gb': memory_total_gb
    }

def track_peak_usage(interval=5, duration=300):
    """
    Track peak CPU and RAM usage over the specified duration.
    
    Args:
        interval (int): Seconds between measurements
        duration (int): Total monitoring duration in seconds
    
    Returns:
        dict: Peak usage data
    """
    logger.info(f"Starting peak usage tracking for {duration}s with {interval}s interval")
    
    start_time = time.time()
    end_time = start_time + duration
    
    peak_data = {
        'start_time': datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
        'peak_cpu_percent': 0,
        'peak_cpu_time': None,
        'peak_memory_percent': 0,
        'peak_memory_time': None,
        'peak_memory_used_gb': 0,
        'memory_total_gb': 0,
        'measurements': []
    }
    
    try:
        while time.time() < end_time:
            current = get_current_usage()
            peak_data['measurements'].append(current)
            
            # Update peak CPU if current is higher
            if current['cpu_percent'] > peak_data['peak_cpu_percent']:
                peak_data['peak_cpu_percent'] = current['cpu_percent']
                peak_data['peak_cpu_time'] = current['timestamp']
                logger.info(f"New peak CPU: {current['cpu_percent']}% at {current['timestamp']}")
            
            # Update peak memory if current is higher
            if current['memory_percent'] > peak_data['peak_memory_percent']:
                peak_data['peak_memory_percent'] = current['memory_percent']
                peak_data['peak_memory_time'] = current['timestamp']
                peak_data['peak_memory_used_gb'] = current['memory_used_gb']
                peak_data['memory_total_gb'] = current['memory_total_gb']
                logger.info(f"New peak RAM: {current['memory_percent']}% ({current['memory_used_gb']:.2f} GB) at {current['timestamp']}")
            
            # Sleep for the interval (adjusted for processing time)
            elapsed = time.time() - start_time
            remaining = min(interval, end_time - time.time())
            if remaining > 0:
                time.sleep(remaining)
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    
    peak_data['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    peak_data['actual_duration'] = time.time() - start_time
    
    return peak_data

def save_peak_data(peak_data):
    """Save peak usage data to a JSON file."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"monitoring/peak_usage_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(peak_data, f, indent=2)
    
    logger.info(f"Peak usage data saved to {filename}")
    return filename

def display_peak_summary(peak_data):
    """Display a summary of peak usage."""
    print("\n===== PEAK USAGE SUMMARY =====\n")
    
    print(f"Monitoring Period: {peak_data['start_time']} to {peak_data['end_time']}")
    print(f"Duration: {peak_data['actual_duration']:.2f} seconds\n")
    
    print(f"Peak CPU Usage: {peak_data['peak_cpu_percent']}%")
    print(f"  Occurred at: {peak_data['peak_cpu_time']}")
    
    print(f"\nPeak RAM Usage: {peak_data['peak_memory_percent']}% ({peak_data['peak_memory_used_gb']:.2f} GB / {peak_data['memory_total_gb']:.2f} GB)")
    print(f"  Occurred at: {peak_data['peak_memory_time']}")
    
    # Calculate average usage
    avg_cpu = sum(m['cpu_percent'] for m in peak_data['measurements']) / len(peak_data['measurements'])
    avg_mem = sum(m['memory_percent'] for m in peak_data['measurements']) / len(peak_data['measurements'])
    
    print(f"\nAverage CPU Usage: {avg_cpu:.2f}%")
    print(f"Average RAM Usage: {avg_mem:.2f}%")
    
    print("\n===============================\n")

def install_dependencies():
    """Install required dependencies."""
    logger.info("Installing required dependencies")
    
    try:
        import psutil
        logger.info("Dependencies already installed")
    except ImportError:
        logger.info("Installing psutil")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        logger.info("Dependencies installed successfully")

def main():
    parser = argparse.ArgumentParser(description="Track peak CPU and RAM usage over time")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between measurements (default: 5)")
    parser.add_argument("--duration", type=int, default=300, help="Total monitoring duration in seconds (default: 300)")
    parser.add_argument("--install", action="store_true", help="Install required dependencies")
    
    args = parser.parse_args()
    
    if args.install:
        install_dependencies()
    
    peak_data = track_peak_usage(interval=args.interval, duration=args.duration)
    filename = save_peak_data(peak_data)
    display_peak_summary(peak_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 