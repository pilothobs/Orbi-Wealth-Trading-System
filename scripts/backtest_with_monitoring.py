#!/usr/bin/env python3

"""
Backtest with Resource Monitoring

This script runs a backtest while simultaneously monitoring system resource usage.
It provides a comprehensive report of both backtest results and system performance.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import threading
import json
import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/backtest_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('backtest_monitor')

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("monitoring").mkdir(exist_ok=True)

def run_peak_usage_monitor(interval=2):
    """
    Run the peak usage monitoring script in a separate process.
    
    Args:
        interval (int): Seconds between measurements
        
    Returns:
        subprocess.Popen: The monitoring process
    """
    logger.info(f"Starting peak usage monitoring with {interval}s interval")
    
    # Generate a unique filename for this monitoring session
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"monitoring/backtest_peak_usage_{timestamp}.json"
    
    # Start the monitoring process without specifying duration (will be terminated later)
    monitor_cmd = [
        sys.executable, 
        "scripts/track_peak_usage.py", 
        "--interval", str(interval),
        "--duration", "86400"  # Set a very long duration (24 hours)
    ]
    
    # Start the process and return it
    process = subprocess.Popen(monitor_cmd)
    logger.info(f"Peak usage monitoring started with PID {process.pid}")
    
    return process

def run_backtest(instrument, period, target_return, max_drawdown):
    """
    Run the ensemble backtest with the specified parameters.
    
    Args:
        instrument (str): The trading instrument to backtest
        period (str): The time period for the backtest
        target_return (float): The target return percentage
        max_drawdown (float): The maximum acceptable drawdown percentage
        
    Returns:
        int: The return code from the backtest process
    """
    logger.info(f"Starting backtest for {instrument} over {period} period")
    
    backtest_cmd = [
        sys.executable,
        "scripts/ensemble_backtest.py",
        "--instrument", instrument,
        "--period", period,
        "--target-return", str(target_return),
        "--max-drawdown", str(max_drawdown)
    ]
    
    # Run the backtest and capture output
    start_time = time.time()
    process = subprocess.run(backtest_cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # Log the results
    duration = end_time - start_time
    logger.info(f"Backtest completed in {duration:.2f} seconds with return code {process.returncode}")
    
    # Save the backtest output to a file
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"logs/backtest_output_{timestamp}.log"
    
    with open(output_file, 'w') as f:
        f.write(process.stdout)
        if process.stderr:
            f.write("\n\nERRORS:\n")
            f.write(process.stderr)
    
    logger.info(f"Backtest output saved to {output_file}")
    
    return process.returncode, duration, output_file

def get_latest_peak_usage_file():
    """Get the most recent peak usage JSON file."""
    peak_files = list(Path("monitoring").glob("peak_usage_*.json"))
    if not peak_files:
        return None
    
    # Sort by modification time (most recent first)
    peak_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return peak_files[0]

def generate_combined_report(backtest_duration, backtest_output_file, peak_usage_file):
    """
    Generate a combined report of backtest results and resource usage.
    
    Args:
        backtest_duration (float): Duration of the backtest in seconds
        backtest_output_file (str): Path to the backtest output log
        peak_usage_file (str): Path to the peak usage JSON file
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"monitoring/backtest_performance_report_{timestamp}.txt"
    
    # Load peak usage data
    peak_data = None
    if peak_usage_file and peak_usage_file.exists():
        with open(peak_usage_file, 'r') as f:
            peak_data = json.load(f)
    
    # Extract key metrics from backtest output
    backtest_metrics = {}
    if os.path.exists(backtest_output_file):
        with open(backtest_output_file, 'r') as f:
            output_lines = f.readlines()
            
            # Look for the summary section
            in_summary = False
            for line in output_lines:
                if "=== Backtest Summary ===" in line:
                    in_summary = True
                    continue
                
                if in_summary and "===" in line:
                    in_summary = False
                    
                if in_summary and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        backtest_metrics[key] = value
    
    # Generate the report
    with open(report_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("BACKTEST PERFORMANCE REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Report generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("BACKTEST METRICS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Duration: {backtest_duration:.2f} seconds\n")
        
        for key, value in backtest_metrics.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n")
        
        if peak_data:
            f.write("SYSTEM RESOURCE USAGE\n")
            f.write("-" * 30 + "\n")
            f.write(f"Monitoring Period: {peak_data['start_time']} to {peak_data['end_time']}\n")
            f.write(f"Peak CPU Usage: {peak_data['peak_cpu_percent']}%\n")
            f.write(f"  Occurred at: {peak_data['peak_cpu_time']}\n\n")
            f.write(f"Peak RAM Usage: {peak_data['peak_memory_percent']}%\n")
            f.write(f"  ({peak_data['peak_memory_used_gb']:.2f} GB / {peak_data['memory_total_gb']:.2f} GB)\n")
            f.write(f"  Occurred at: {peak_data['peak_memory_time']}\n\n")
            
            # Calculate average usage
            if peak_data['measurements']:
                avg_cpu = sum(m['cpu_percent'] for m in peak_data['measurements']) / len(peak_data['measurements'])
                avg_mem = sum(m['memory_percent'] for m in peak_data['measurements']) / len(peak_data['measurements'])
                
                f.write(f"Average CPU Usage: {avg_cpu:.2f}%\n")
                f.write(f"Average RAM Usage: {avg_mem:.2f}%\n")
        else:
            f.write("No resource usage data available.\n")
        
        f.write("\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Combined performance report saved to {report_file}")
    return report_file

def main():
    parser = argparse.ArgumentParser(description="Run a backtest with system resource monitoring")
    parser.add_argument("--instrument", type=str, default="EUR_USD", help="Trading instrument (default: EUR_USD)")
    parser.add_argument("--period", type=str, default="6m", help="Backtest period (default: 6m)")
    parser.add_argument("--target-return", type=float, default=0.20, help="Target return percentage (default: 0.20)")
    parser.add_argument("--max-drawdown", type=float, default=0.10, help="Maximum drawdown percentage (default: 0.10)")
    parser.add_argument("--monitor-interval", type=int, default=2, help="Monitoring interval in seconds (default: 2)")
    
    args = parser.parse_args()
    
    try:
        # Start the resource monitoring
        monitor_process = run_peak_usage_monitor(interval=args.monitor_interval)
        
        # Give the monitor a moment to start
        time.sleep(2)
        
        # Run the backtest
        return_code, duration, output_file = run_backtest(
            args.instrument, 
            args.period, 
            args.target_return, 
            args.max_drawdown
        )
        
        # Stop the monitoring process
        monitor_process.terminate()
        monitor_process.wait()
        
        # Wait a moment for the monitoring data to be saved
        time.sleep(2)
        
        # Get the latest peak usage file
        peak_file = get_latest_peak_usage_file()
        
        # Generate the combined report
        report_file = generate_combined_report(duration, output_file, peak_file)
        
        # Display the report
        print(f"\nBacktest completed. Performance report saved to: {report_file}\n")
        with open(report_file, 'r') as f:
            print(f.read())
        
        return return_code
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        # Ensure the monitoring process is terminated
        if 'monitor_process' in locals():
            monitor_process.terminate()
        return 1
    except Exception as e:
        logger.error(f"Error during backtest monitoring: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 