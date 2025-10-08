"""
Clock skew analysis and Date extrapolation.

`python plot-clock-skew.py --extrapolate "2026-03-15 12:00:00"`
"""

import os
import json
import datetime
import argparse
from dateutil import parser as date_parser

import numpy as np
import matplotlib.pyplot as plt

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze blockchain clock skew and extrapolate block numbers')
    parser.add_argument('--extrapolate', type=str, 
                       help='Extrapolate block number for a given timestamp. Assumes UTC if no timezone specified (e.g., "2025-03-15 12:00:00", "2025-03-15T12:00:00Z", or "2025-03-15 12:00:00+01:00")')
    return parser.parse_args()

def extrapolate_block_number(data, target_timestamp, average_drift, block_time=6.0):
    """
    Extrapolate block number for a given timestamp based on drift analysis
    
    Args:
        data: List of (block_number, timestamp_ms) tuples
        target_timestamp: Target timestamp in seconds since epoch
        average_drift: Average drift in minutes per day
        block_time: Expected block time in seconds (default: 6s for Kusama/Polkadot)
    """
    # Sort data by block number and get the most recent point
    data_sorted = sorted(data, key=lambda x: x[0])
    latest_block, latest_timestamp_ms = data_sorted[-1]
    latest_timestamp = latest_timestamp_ms / 1000  # Convert to seconds
    
    # Calculate time difference
    time_diff_seconds = target_timestamp - latest_timestamp
    time_diff_days = time_diff_seconds / (24 * 3600)
    
    print(f"\nExtrapolation Analysis:")
    print(f"Latest known data point: Block {latest_block} at {datetime.datetime.fromtimestamp(latest_timestamp, tz=datetime.timezone.utc)}")
    print(f"Target timestamp: {datetime.datetime.fromtimestamp(target_timestamp, tz=datetime.timezone.utc)}")
    print(f"Time difference: {time_diff_days:.2f} days ({time_diff_seconds:.0f} seconds)")
    
    # Calculate expected blocks without drift
    expected_blocks = time_diff_seconds / block_time
    
    # Apply drift correction
    # Drift is in minutes/day, convert to seconds/day
    drift_seconds_per_day = average_drift * 60
    total_drift_seconds = drift_seconds_per_day * time_diff_days
    
    # Adjust for drift (positive drift means chain is slower, so fewer blocks)
    drift_adjusted_seconds = time_diff_seconds - total_drift_seconds
    drift_adjusted_blocks = drift_adjusted_seconds / block_time
    
    estimated_block = latest_block + int(round(drift_adjusted_blocks))
    
    print(f"Expected blocks without drift: {expected_blocks:.0f}")
    print(f"Average drift: {average_drift:.2f} minutes/day")
    print(f"Total drift over {time_diff_days:.2f} days: {total_drift_seconds:.0f} seconds")
    print(f"Drift-adjusted blocks: {drift_adjusted_blocks:.0f}")
    print(f"Estimated block number: {estimated_block}")
    
    return estimated_block

START = 28099885 # Start block. Should be anchored on a common timestamp, like 2025-02-20 00:00:00
QUERIES  = 30 # How many times to query. One relay year is 3650 queries.
DIFF     = 14400 # How many blocks to skip in between each query. Set to one relay day.

def main():
    args = parse_arguments()

    chain = SubstrateInterface(url="wss://rpc.polkadot.io")
    print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

    data = []
    PATH = f"clock-skew-{chain.name}.json"

    # Load existing data or collect new data
    if os.path.exists(PATH):
        with open(PATH, 'r') as f:
            data = json.load(f)
    else:
        for i in range(QUERIES+1):
            block_number = START - i * DIFF

            if any(d[0] == block_number for d in data):
                continue

            print(f"Querying block {block_number}")
            block_hash = chain.get_block_hash(block_number)

            try:
                now = chain.query("Timestamp", "Now", [], block_hash=block_hash)
            except SubstrateRequestException as e:
                print(f"Failed to timestamp: {e}")
                break

            print(f"[{block_number}] Timestamp: {now}, hash: {block_hash}")
            data.append((block_number, now.value))

    # Write to json
    with open(PATH, 'w') as f:
        json.dump(data, f, indent=4)

    if not data:
        print("No data available for analysis")
        return

    # Sort by block number
    data = sorted(data, key=lambda x: x[0])
    # Convert timestamps to date
    y_date = [datetime.datetime.fromtimestamp(d[1] / 1000) for d in data]
    # Count up dates from the first date
    first_date = y_date[0]
    y_calendar = [first_date + datetime.timedelta(days=i) for i in range(len(y_date))]

    # Calculate delta from date and calendar
    y_delta = [(y_calendar[i] - y_date[i]).total_seconds() / 60 for i in range(len(y_date))]

    # Calculate derivative of y_delta (drift per day)
    y_drift = np.diff(y_delta)  # Change in delta between consecutive days
    y_calendar_drift = y_calendar[1:]  # Remove first element to match drift array length

    # Calculate and print average drift per day
    average_drift = np.mean(y_drift)
    print(f"\nAverage drift per day: {average_drift:.2f} minutes/day")

    # Handle extrapolation if requested
    if args.extrapolate:
        try:
            # Parse the timestamp string
            target_dt = date_parser.parse(args.extrapolate)
            # Convert to UTC if not timezone-aware
            if target_dt.tzinfo is None:
                target_dt = target_dt.replace(tzinfo=datetime.timezone.utc)
                print(f"Assuming UTC timezone for: {target_dt}")
            else:
                print(f"Using provided timezone: {target_dt}")
            
            target_timestamp = target_dt.timestamp()
            estimated_block = extrapolate_block_number(data, target_timestamp, average_drift)
            
            print(f"\n🎯 Estimated block number for {args.extrapolate}: {estimated_block}")
            
        except Exception as e:
            print(f"Error parsing timestamp '{args.extrapolate}': {e}")
            print("Please use format like '2025-03-15 12:00:00' (assumes UTC) or '2025-03-15T12:00:00Z'")
            return

    # Also print delta to console
    for i in range(len(y_delta)):
        print(f"{y_calendar[i]} - {y_date[i]} = {y_delta[i]} minutes")

    # Print drift data
    print("\nDrift per day:")
    for i in range(len(y_drift)):
        print(f"Day {i+1}: {y_drift[i]:.2f} minutes/day")

    # Create the plot
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Plot chain time vs calendar time
    ax1.plot(y_calendar, y_date, color='#e9d758', label='Chain')
    ax1.plot(y_calendar, y_calendar, color='#297373', linestyle=(0, (5, 9)), label='Calendar')
    ax1.legend(loc='upper left')
    ax1.set_xlabel('Calendar Date')
    ax1.set_ylabel('Chain Time', color='red')

    # Second Y scale on the right for the delta
    ax2 = ax1.twinx()
    ax2.set_ylabel('Delta (minutes)', color='#f87575')
    ax2.tick_params(axis='y', labelcolor='#f87575')
    ax2.plot(y_calendar, y_delta, color='#f87575', marker='o', markersize=3, label='Delta (minutes)')

    # Reference lines for delta
    for i in range(3):
        min_val = (i + 1) * 10
        y_minus = [-min_val * j for j in range(len(y_calendar))]
        ax2.plot(y_calendar, y_minus, color='#ffa9a3', linestyle='--', alpha=0.8, label=f'-{min_val} min/day trend')

    # Third Y scale for drift rate (derivative)
    ax3 = ax1.twinx()
    # Offset the third axis to the right
    ax3.spines['right'].set_position(('outward', 60))
    ax3.set_ylabel('Drift Rate (minutes/day)', color='#5c95ff')
    ax3.tick_params(axis='y', labelcolor='#5c95ff')
    ax3.plot(y_calendar_drift, y_drift, color='#5c95ff', linestyle='dotted', linewidth=1, label='Drift Rate')

    # Add the filled area between zero and the drift rate line
    ax3.fill_between(y_calendar_drift, 0, y_drift, color='#5c95ff', alpha=0.1, label='Integrated Drift Area')

    # Add a horizontal line at y=0 for the drift rate
    ax3.axhline(y=0, color='blue', linestyle=':', alpha=0.5, linewidth=1)

    # Set up legends
    ax2.legend(loc='upper right')
    ax3.legend(loc='center right')

    # Add grid for better readability
    ax1.grid(True, alpha=0.3)

    plt.title(f'Clock Skew Analysis for Polkadot\nAverage Drift: {average_drift:.2f} min/day')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
