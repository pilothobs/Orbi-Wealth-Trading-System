# Utility Scripts for Orbi Wealth Trading System

This directory contains utility scripts for backup, monitoring, and maintenance of the Orbi Wealth Trading System.

## Backup Scripts

### `auto_backup.py`

This script creates a backup of the trading system and uploads it to AWS S3.

**Features:**
- Creates a timestamped ZIP backup of the trading system
- Uploads the backup to AWS S3
- Maintains a specified number of backups locally and in S3
- Logs all backup activities

**Usage:**
```bash
python auto_backup.py
```

### `setup_backup_cron.py`

This script sets up a cron job to run the `auto_backup.py` script at specified intervals.

**Features:**
- Installs required dependencies
- Sets up a cron job to run the backup script
- Supports different backup frequencies (hourly, daily, weekly, monthly)

**Usage:**
```bash
python setup_backup_cron.py [interval]
```

Where `interval` is one of: `hourly`, `daily`, `weekly`, `monthly`. Default is `daily`.

### `check_backup_status.py`

This script checks the status of backups in the AWS S3 bucket and locally.

**Features:**
- Lists local backups with size and date
- Lists S3 backups with size and date
- Checks for issues with the backup system

**Usage:**
```bash
python check_backup_status.py
```

## System Monitoring Scripts

### `monitor_system_resources.py`

This script monitors system resources (CPU, memory, disk) and logs the information.

**Features:**
- Monitors CPU, memory, disk, and network usage
- Tracks top processes by CPU and memory usage
- Saves metrics to JSON files
- Displays a summary of system resources
- Can run continuously or as a one-time check

**Usage:**
```bash
# One-time check
python monitor_system_resources.py

# Continuous monitoring
python monitor_system_resources.py --continuous --interval 60

# Install dependencies and run
python monitor_system_resources.py --install

# Run for a specific duration (in seconds)
python monitor_system_resources.py --continuous --duration 3600
```

### `track_peak_usage.py`

This script specifically tracks peak CPU and RAM usage over a specified period.

**Features:**
- Records the highest CPU and RAM usage observed during monitoring
- Logs when new peak values are detected
- Saves detailed measurements to a JSON file
- Displays a summary with peak and average usage statistics
- Configurable monitoring duration and interval

**Usage:**
```bash
# Track peak usage for 5 minutes (default)
python track_peak_usage.py

# Track with custom interval and duration
python track_peak_usage.py --interval 10 --duration 600

# Install dependencies and run
python track_peak_usage.py --install
```

### `backtest_with_monitoring.py`

This script runs a backtest while simultaneously monitoring system resource usage, providing a comprehensive report of both backtest results and system performance.

**Features:**
- Runs an ensemble backtest with specified parameters
- Monitors CPU and RAM usage during the backtest
- Captures peak resource usage
- Generates a detailed performance report combining backtest results and resource metrics
- Saves backtest output and monitoring data for future reference

**Usage:**
```bash
# Run with default parameters
python backtest_with_monitoring.py

# Run with custom parameters
python backtest_with_monitoring.py --instrument EUR_USD --period 1y --target-return 0.25 --max-drawdown 0.15 --monitor-interval 5
```

### `setup_monitor_cron.py`

This script sets up a cron job to run the `monitor_system_resources.py` script at specified intervals.

**Features:**
- Installs required dependencies
- Sets up a cron job to run the monitoring script
- Configurable monitoring frequency

**Usage:**
```bash
python setup_monitor_cron.py [interval]
```

Where `interval` is the number of minutes between monitoring checks. Default is 15 minutes.

## Configuration

All scripts use the environment variables defined in the `.env` file at the root of the project. Make sure this file is properly configured before running the scripts.

Required environment variables for backup scripts:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: Your preferred AWS region
- `S3_BUCKET_NAME`: Your S3 bucket name
- `MAX_BACKUPS`: Maximum number of backups to keep (default: 5)
- `INCLUDE_VENV`: Whether to include the virtual environment in backups (default: False)

## Logs

All scripts log their activities to the `logs` directory. Check these logs for detailed information about script execution and any errors that may have occurred. 