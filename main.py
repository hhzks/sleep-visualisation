"""
Sleep Log Visualization
Main application entry point.

This program retrieves sleep logs from the Google Health API and creates
visualizations showing sleep periods throughout each day.

Usage:
    python main.py                    # Get last 30 days of sleep data
    python main.py --days 7           # Get last 7 days
    python main.py --start 2026-06-01 --end 2026-06-18  # Specific date range
    python main.py --demo             # Run with demo data (no API needed)
"""

import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
import sys

from google_auth import authenticate
from sleep_api import GoogleHealthSleepAPI, parse_sleep_data
from sleep_chart import (
    create_sleep_chart,
    create_sleep_duration_chart,
    create_sleep_stages_summary,
    create_all_charts
)


def get_demo_data():
    """Generate demo data for testing without API access."""
    import random
    
    records = []
    base_date = datetime.now()
    
    for i in range(14):
        date = base_date - timedelta(days=i)
        
        # Random sleep start between 10 PM and 1 AM
        start_hour = random.randint(22, 25) % 24
        start_minute = random.randint(0, 59)
        
        # Random sleep duration between 5 and 9 hours
        duration_hours = random.uniform(5, 9)
        
        if start_hour >= 22:
            start_date = date - timedelta(days=1)
        else:
            start_date = date
        
        start_time = start_date.replace(hour=start_hour, minute=start_minute, second=0)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Generate random sleep stages
        total_minutes = int(duration_hours * 60)
        deep = random.randint(int(total_minutes * 0.1), int(total_minutes * 0.25))
        rem = random.randint(int(total_minutes * 0.15), int(total_minutes * 0.25))
        wake = random.randint(int(total_minutes * 0.03), int(total_minutes * 0.1))
        light = total_minutes - deep - rem - wake
        
        # Generate detailed levels data
        levels_data = []
        current_time = start_time
        remaining = total_minutes
        
        stages = ['light', 'deep', 'light', 'rem', 'light', 'deep', 'light', 'rem', 'light']
        for stage in stages:
            if remaining <= 0:
                break
            duration = min(random.randint(15, 90), remaining)
            levels_data.append({
                'dateTime': current_time.isoformat(),
                'level': stage,
                'seconds': duration * 60
            })
            current_time += timedelta(minutes=duration)
            remaining -= duration
        
        record = {
            'log_id': f'demo_{i}',
            'date_of_sleep': date.strftime('%Y-%m-%d'),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_ms': int(duration_hours * 3600000),
            'duration_hours': duration_hours,
            'efficiency': random.randint(85, 98),
            'is_main_sleep': True,
            'minutes_asleep': int(duration_hours * 60 - wake),
            'minutes_awake': wake,
            'time_in_bed': int(duration_hours * 60),
            'type': 'stages',
            'stages_summary': {
                'deep': deep,
                'light': light,
                'rem': rem,
                'wake': wake,
            },
            'levels_data': levels_data,
        }
        records.append(record)
    
    return records


def print_sleep_summary(records):
    """Print a summary of sleep records to console."""
    if not records:
        print("No sleep records found.")
        return
    
    print("\n" + "="*60)
    print("SLEEP LOG SUMMARY")
    print("="*60)
    
    main_sleep = [r for r in records if r.get('is_main_sleep', True)]
    
    print(f"\nTotal records: {len(records)}")
    print(f"Main sleep records: {len(main_sleep)}")
    
    if main_sleep:
        durations = [r['duration_hours'] for r in main_sleep]
        avg_duration = sum(durations) / len(durations)
        
        print(f"\nSleep Duration Statistics:")
        print(f"  Average: {avg_duration:.1f} hours")
        print(f"  Minimum: {min(durations):.1f} hours")
        print(f"  Maximum: {max(durations):.1f} hours")
    
    print("\nRecent Sleep Records:")
    print("-" * 60)
    
    for record in sorted(main_sleep, key=lambda x: x['date_of_sleep'], reverse=True)[:10]:
        date = record['date_of_sleep']
        duration = record['duration_hours']
        efficiency = record.get('efficiency')
        if efficiency is None:
            efficiency = 'N/A'
        
        start = record.get('start_time', '')
        if start:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            start_str = start_time.strftime('%I:%M %p')
        else:
            start_str = 'N/A'
        
        print(f"  {date}: {duration:.1f} hrs | Started: {start_str} | Efficiency: {efficiency}%")
    
    print("-" * 60)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Retrieve and visualize Google Health sleep data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Get last 30 days of sleep data
  python main.py --days 7           Get last 7 days
  python main.py --start 2026-06-01 --end 2026-06-18
                                    Get specific date range
  python main.py --demo             Run with demo data (no API needed)
  python main.py --no-display       Save charts but don't display them
  python main.py --width 1600 --height 900
                                    Save charts at exactly 1600x900 pixels
        """
    )
    
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of sleep data to retrieve (default: 30)')
    parser.add_argument('--start', type=str,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--demo', action='store_true',
                       help='Use demo data instead of API')
    parser.add_argument('--output', type=str, default='.',
                       help='Output directory for chart images')
    parser.add_argument('--no-display', action='store_true',
                       help='Save charts but do not display them')
    parser.add_argument('--no-save', action='store_true',
                       help='Display charts but do not save them')
    parser.add_argument('--single-color', type=str, default="#4809db",
                       help='Use a single color for all sleep periods (e.g., "blue" or "#2196f3")')
    
    parser.add_argument('--width', type=int,
                       help='Image width in pixels (default: chart-specific)')
    parser.add_argument('--height', type=int,
                       help='Image height in pixels (default: chart-specific)')
    parser.add_argument('--dpi', type=int, default=150,
                       help='Image resolution in dots per inch (default: 150)')
    
    args = parser.parse_args()
    size = {'width': args.width, 'height': args.height, 'dpi': args.dpi}
    
    # Create output directory if needed
    if not args.no_save and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Get sleep data
    if args.demo:
        print("Running in demo mode with generated data...")
        sleep_records = get_demo_data()
    else:
        # Authenticate with Google
        print("Authenticating with Google Health...")
        access_token = authenticate()
        
        if not access_token:
            print("Authentication failed. Exiting.")
            sys.exit(1)
        
        # Create API client
        api = GoogleHealthSleepAPI(access_token)
        
        try:
            if args.start and args.end:
                print(f"Retrieving sleep data from {args.start} to {args.end}...")
                data = api.get_sleep_log_range(args.start, args.end)
            else:
                print(f"Retrieving last {args.days} days of sleep data...")
                data = api.get_recent_sleep_logs(days=args.days)
            
            sleep_records = parse_sleep_data(data)
            
        except Exception as e:
            print(f"Error retrieving sleep data: {e}")
            sys.exit(1)
    
    # Print summary
    print_sleep_summary(sleep_records)
    
    # Determine date range for charts
    if args.start and args.end:
        chart_start_date = args.start
        chart_end_date = args.end
    else:
        chart_end_date = datetime.now().strftime('%Y-%m-%d')
        chart_start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    # Create charts
    print("\nGenerating visualizations...")
    
    if args.no_save:
        # Just display, don't save
        create_sleep_chart(sleep_records, "Sleep Periods by Day", single_color=args.single_color,
                          start_date=chart_start_date, end_date=chart_end_date, **size)
        create_sleep_duration_chart(sleep_records, "Sleep Duration Over Time", **size)
        create_sleep_stages_summary(sleep_records, "Sleep Stages Distribution", **size)
    else:
        # Save to files
        create_all_charts(sleep_records, args.output, single_color=args.single_color,
                         start_date=chart_start_date, end_date=chart_end_date, **size)
    
    if not args.no_display:
        print("\nDisplaying charts...")
        plt.show()
    
    print("\nDone!")


if __name__ == "__main__":
    main()
