#!/usr/bin/env python3
"""
Binance Candles Script - Fetches cryptocurrency candle data from Binance API

USAGE:
1. Activate the virtual environment:
   source venv/bin/activate

2. Install dependencies (if not already installed):
   pip install requests plotext

3. Run the script:
   python binance_candles.py [OPTIONS]

OPTIONS:
   --symbol SYMBOL         Trading pair symbol (default: BTCUSDT)
   --timeframe TIMEFRAME   Candle timeframe: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M (default: 1m)
   --limit LIMIT           Number of candles to fetch (default: 100, max: 1000)
   --dark                  Enable dark mode for better terminal visibility
   --once                  Run once and exit (default: continuous mode)

EXAMPLES:
   python binance_candles.py --symbol ETHUSDT --timeframe 1h --limit 50
   python binance_candles.py --dark --symbol ADAUSDT --timeframe 15m
   python binance_candles.py --once

The script runs continuously and refreshes data at appropriate intervals:
- For minute intervals: refreshes every minute at :00 seconds
- For hour intervals: refreshes every hour at :00 minutes
- For day intervals: refreshes every day at 00:00
"""

import requests
import json
import sys
import argparse
import time
import os
from datetime import datetime, timedelta
import plotext as plt


def fetch_binance_candles(symbol="BTCUSDT", interval="1m", limit=100):
    """
    Fetch cryptocurrency candle data from Binance API and return processed data.
    """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        # Make the API request
        response = requests.get(url)
        
        # Check HTTP status
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code} - Failed to fetch data from Binance API", file=sys.stderr)
            sys.exit(1)
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from Binance API", file=sys.stderr)
            sys.exit(1)
        
        # Validate JSON shape - should be a list of lists
        if not isinstance(data, list) or len(data) == 0:
            print("Error: Unexpected data format from Binance API", file=sys.stderr)
            sys.exit(1)
        
        # Check if first item has expected structure (should be a list with at least 6 elements)
        if not isinstance(data[0], list) or len(data[0]) < 6:
            print("Error: Unexpected candle data format from Binance API", file=sys.stderr)
            sys.exit(1)
        
        # Process candle data
        processed_data = []
        for candle in data:
            try:
                # Extract candle data
                timestamp_ms = int(candle[0])
                open_price = float(candle[1])
                high_price = float(candle[2])
                low_price = float(candle[3])
                close_price = float(candle[4])
                volume = float(candle[5])
                
                # Convert timestamp from milliseconds to human-readable format
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                processed_data.append({
                    'timestamp': timestamp,
                    'timestamp_str': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
                
            except (ValueError, IndexError) as e:
                print(f"Error: Invalid candle data format: {e}", file=sys.stderr)
                sys.exit(1)
        
        return processed_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error: Network request failed - {e}", file=sys.stderr)
        sys.exit(1)


def display_table(data):
    """
    Display candle data in formatted table.
    """
    print(f"{'Timestamp':<20} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12} {'Volume':<15}")
    print("-" * 95)
    
    for candle in data:
        print(f"{candle['timestamp_str']:<20} {candle['open']:<12.2f} {candle['high']:<12.2f} {candle['low']:<12.2f} {candle['close']:<12.2f} {candle['volume']:<15.2f}")


def display_candlestick_chart(data, symbol, timeframe, dark_mode=False):
    """
    Display candlestick chart using plotext.
    """
    # Prepare data for plotting - plotext candlestick expects specific format
    dates = list(range(len(data)))
    candle_data = {
        "Open": [candle['open'] for candle in data],
        "High": [candle['high'] for candle in data],
        "Low": [candle['low'] for candle in data],
        "Close": [candle['close'] for candle in data]
    }

    # Clear any previous plots
    plt.clear_data()
    plt.clear_figure()

    # Set dark mode colors if requested
    if dark_mode:
        plt.theme('dark')
    else:
        plt.theme('default')

    # Create candlestick plot
    plt.candlestick(dates, candle_data)

    # Set plot properties
    interval_name = get_interval_display_name(timeframe)
    interval_minutes = get_interval_seconds(timeframe) // 60
    total_minutes = len(data) * interval_minutes
    if total_minutes >= 1440 and total_minutes % 1440 == 0:
        time_span = f"{total_minutes // 1440} Days"
    elif total_minutes >= 60 and total_minutes % 60 == 0:
        time_span = f"{total_minutes // 60} Hours"
    else:
        time_span = f"{total_minutes} Minutes"
    plt.title(f"{symbol} - Last {time_span} ({len(data)} candles) - Timeframe: {timeframe}")
    plt.xlabel(f"Time ({interval_name} ago)")
    plt.ylabel(f"Price ({symbol[-4:] if len(symbol) >= 4 else 'USDT'})")

    # Set x-axis labels to show every 10th data point
    x_labels = []
    x_positions = []
    step = max(1, len(data) // 10)
    for i in range(0, len(data), step):
        periods_ago = len(data) - i - 1
        x_labels.append(f"-{periods_ago}")
        x_positions.append(i)

    plt.xticks(x_positions, x_labels)

    # Show the plot
    plt.show()


def get_interval_display_name(interval):
    """
    Convert interval code to display name.
    """
    interval_names = {
        '1m': 'Minutes', '3m': 'Minutes', '5m': 'Minutes', '15m': 'Minutes', '30m': 'Minutes',
        '1h': 'Hours', '2h': 'Hours', '4h': 'Hours', '6h': 'Hours', '8h': 'Hours', '12h': 'Hours',
        '1d': 'Days', '3d': 'Days', '1w': 'Weeks', '1M': 'Months'
    }
    return interval_names.get(interval, 'Periods')


def get_interval_seconds(interval):
    """
    Convert interval to seconds for sleep calculation.
    """
    interval_seconds = {
        '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
        '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800, '12h': 43200,
        '1d': 86400, '3d': 259200, '1w': 604800, '1M': 2592000  # Approximate for month
    }
    return interval_seconds.get(interval, 60)


def calculate_next_update_time(interval):
    """
    Calculate when the next update should occur based on interval.
    """
    now = datetime.now()
    
    if interval.endswith('m'):
        # For minute intervals, wait until next minute at :00 seconds
        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        return next_minute
    elif interval.endswith('h'):
        # For hour intervals, wait until next hour at :00 minutes
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour
    elif interval.endswith('d'):
        # For day intervals, wait until next day at 00:00
        next_day = (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
        return next_day
    else:
        # For other intervals, use the interval duration
        return now + timedelta(seconds=get_interval_seconds(interval))


def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system('clear' if os.name == 'posix' else 'cls')


def display_data(symbol, timeframe, limit, dark_mode):
    """
    Fetch and display both table and chart data.
    """
    try:
        print(f"Fetching {symbol} candle data from Binance...\n")
        data = fetch_binance_candles(symbol, timeframe, limit)

        print("=" * 95)
        print("TABULAR DATA")
        print("=" * 95)
        display_table(data)

        print("\n" + "=" * 95)
        print("CANDLESTICK CHART")
        print("=" * 95)
        display_candlestick_chart(data, symbol, timeframe, dark_mode)
        
        return True
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        return False


def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Fetch and display cryptocurrency candle data from Binance API',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--symbol', default='BTCUSDT',
                       help='Trading pair symbol (default: BTCUSDT)')
    parser.add_argument('--timeframe', default='1m',
                       choices=['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
                       help='Candle timeframe (default: 1m)')
    parser.add_argument('--limit', type=int, default=100,
                       help='Number of candles to fetch (default: 100, max: 1000)')
    parser.add_argument('--dark', action='store_true',
                       help='Enable dark mode for better terminal visibility')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (default: continuous mode)')
    
    args = parser.parse_args()
    
    # Validate limit
    if args.limit < 1 or args.limit > 1000:
        parser.error('Limit must be between 1 and 1000')
    
    return args


def main():
    """Main function to run the script."""
    args = parse_arguments()
    
    print(f"Starting Binance Candles Monitor")
    print(f"Symbol: {args.symbol}, Timeframe: {args.timeframe}, Limit: {args.limit}")
    print(f"Dark Mode: {args.dark}, Continuous: {not args.once}")
    print("-" * 60)

    if args.once:
        # Run once and exit
        display_data(args.symbol, args.timeframe, args.limit, args.dark)
    else:
        # Continuous mode
        print(f"Running in continuous mode. Press Ctrl+C to exit.\n")

        first_run = True
        while True:
            try:
                if not first_run:
                    clear_screen()

                # Calculate next update time
                next_update = calculate_next_update_time(args.timeframe)
                sleep_seconds = (next_update - datetime.now()).total_seconds()

                # Display current time and timing info at the top
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"Last updated: {current_time}")
                print(f"Symbol: {args.symbol}, Timeframe: {args.timeframe}, Limit: {args.limit}")
                print(f"Next update: {next_update.strftime('%Y-%m-%d %H:%M:%S')} (in {sleep_seconds:.0f}s)")
                print("-" * 60)

                # Fetch and display data
                success = display_data(args.symbol, args.timeframe, args.limit, args.dark)
                
                if not success:
                    print("Failed to fetch data. Retrying in 60 seconds...")
                    time.sleep(60)
                    continue
                
                first_run = False
                
                # Sleep until next update
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                print("\n\nExiting... Goodbye!")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}", file=sys.stderr)
                print("Retrying in 60 seconds...")
                time.sleep(60)


if __name__ == "__main__":
    main()
