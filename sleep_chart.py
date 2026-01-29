"""
Sleep Chart Visualization Module
Creates charts displaying sleep periods throughout each day.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import numpy as np


# Color scheme for sleep stages
SLEEP_COLORS = {
    'deep': '#1a237e',      # Dark blue
    'light': '#64b5f6',     # Light blue
    'rem': '#7b1fa2',       # Purple
    'wake': '#ffab00',      # Amber
    'asleep': '#2196f3',    # Blue (for classic tracking)
    'restless': '#ff9800',  # Orange
    'awake': '#f44336',     # Red
}


def time_to_hours(time_str):
    """Convert ISO time string to hours since midnight."""
    dt = date_parser.parse(time_str)
    return dt.hour + dt.minute / 60 + dt.second / 3600


def create_sleep_chart(sleep_records, title="Sleep Log Visualization", save_path=None, single_color=None, start_date=None, end_date=None):
    """
    Create a horizontal bar chart showing sleep periods for each day.
    
    Args:
        sleep_records: List of parsed sleep records from parse_sleep_data()
        title: Chart title
        save_path: Optional path to save the chart
        single_color: Optional color to use for all sleep periods (e.g., '#2196f3' or 'blue').
                      If None, uses different colors for each sleep stage.
        start_date: Optional start date string (YYYY-MM-DD) for the date range to display.
        end_date: Optional end date string (YYYY-MM-DD) for the date range to display.
    
    Returns:
        matplotlib figure object
    """
    if not sleep_records and not (start_date and end_date):
        print("No sleep records to display")
        return None
    
    # Group records by date, keeping track of all sleep data for each date
    records_by_date = {}
    for record in sleep_records:
        date = record['date_of_sleep']
        if date not in records_by_date:
            records_by_date[date] = []
        records_by_date[date].append(record)
    
    # Determine date range
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    elif sleep_records:
        all_dates = [datetime.strptime(r['date_of_sleep'], '%Y-%m-%d') for r in sleep_records]
        start_dt = min(all_dates)
        end_dt = max(all_dates)
    else:
        print("No sleep records to display")
        return None
    
    # Generate all dates in range
    all_dates = []
    current = start_dt
    while current <= end_dt:
        all_dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, max(6, len(all_dates) * 0.3)))
    
    # Y-axis: all dates in range
    y_positions = range(len(all_dates))
    
    # Track legend items
    legend_items = {}
    
    # Helper function to convert datetime to chart hours
    def to_chart_hours(dt):
        hours = dt.hour + dt.minute / 60
        return hours
    
    for idx, date in enumerate(all_dates):
        if date not in records_by_date:
            # No sleep data for this date - leave row empty
            continue
        
        # Process all sleep records for this date
        for record in records_by_date[date]:
            if record.get('levels_data'):
                # Detailed sleep stages available
                for level in record['levels_data']:
                    level_start = date_parser.parse(level['dateTime'])
                    level_duration_min = level['seconds'] / 60
                    level_type = level['level']
                    
                    start_hour = to_chart_hours(level_start)
                    duration_hours = level_duration_min / 60
                    
                    if single_color:
                        color = single_color
                        legend_label = 'Sleep'
                    else:
                        color = SLEEP_COLORS.get(level_type, '#9e9e9e')
                        legend_label = level_type
                    
                    bar = ax.barh(idx, duration_hours, left=start_hour, height=0.6,
                                 color=color, edgecolor='white', linewidth=0.5)
                    
                    if legend_label not in legend_items:
                        legend_items[legend_label] = color
            else:
                # Classic tracking - just show sleep period as a single bar
                start_time = date_parser.parse(record['start_time'])
                end_time = date_parser.parse(record['end_time'])
                
                start_hour = to_chart_hours(start_time)
                
                # Calculate duration
                duration = (end_time - start_time).total_seconds() / 3600
                
                color = single_color if single_color else SLEEP_COLORS['asleep']
                
                bar = ax.barh(idx, duration, left=start_hour, height=0.6,
                             color=color, edgecolor='white', linewidth=0.5)
                
                if 'Sleep' not in legend_items:
                    legend_items['Sleep'] = color
    
    # Configure axes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(all_dates)
    ax.set_ylabel('Date')
    
    # X-axis: hours (midnight to midnight = 24 hours)
    ax.set_xlim(0, 24)
    ax.set_xlabel('Time')
    
    # Create hour labels
    hour_labels = []
    hour_positions = []
    for h in range(0, 25, 2):
        hour_labels.append(f"{h:02d}:00")
        hour_positions.append(h)
    
    ax.set_xticks(hour_positions)
    ax.set_xticklabels(hour_labels, rotation=45, ha='right')
    
    # Add vertical lines for key times
    ax.axvline(x=6, color='gray', linestyle=':', alpha=0.5, label='6 AM')
    ax.axvline(x=12, color='gray', linestyle='--', alpha=0.5, label='Noon')
    
    # Add legend
    legend_patches = [mpatches.Patch(color=color, label=label.capitalize()) 
                     for label, color in legend_items.items()]
    ax.legend(handles=legend_patches, loc='upper right', framealpha=0.9)
    
    # Title and grid
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Invert y-axis so most recent date is at top
    ax.invert_yaxis()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    return fig


def create_sleep_duration_chart(sleep_records, title="Sleep Duration Over Time", save_path=None):
    """
    Create a line chart showing sleep duration for each day.
    
    Args:
        sleep_records: List of parsed sleep records
        title: Chart title
        save_path: Optional path to save the chart
    
    Returns:
        matplotlib figure object
    """
    if not sleep_records:
        print("No sleep records to display")
        return None
    
    # Filter to main sleep only and sort by date
    main_sleep = [r for r in sleep_records if r.get('is_main_sleep', True)]
    main_sleep = sorted(main_sleep, key=lambda x: x['date_of_sleep'])
    
    dates = [datetime.strptime(r['date_of_sleep'], '%Y-%m-%d') for r in main_sleep]
    durations = [r['duration_hours'] for r in main_sleep]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot line and scatter
    ax.plot(dates, durations, 'b-', linewidth=2, alpha=0.7)
    ax.scatter(dates, durations, c='blue', s=50, zorder=5)
    
    # Add 8-hour reference line
    ax.axhline(y=8, color='green', linestyle='--', alpha=0.7, label='8 hours (recommended)')
    ax.axhline(y=7, color='orange', linestyle='--', alpha=0.5, label='7 hours (minimum)')
    
    # Fill area under curve
    ax.fill_between(dates, durations, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
    plt.xticks(rotation=45, ha='right')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Sleep Duration (hours)')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Set y-axis limits
    ax.set_ylim(0, max(12, max(durations) + 1))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    return fig


def create_sleep_stages_summary(sleep_records, title="Sleep Stages Summary", save_path=None):
    """
    Create a stacked bar chart showing sleep stage distribution per day.
    
    Args:
        sleep_records: List of parsed sleep records with stages data
        title: Chart title
        save_path: Optional path to save the chart
    
    Returns:
        matplotlib figure object
    """
    # Filter records with stages data
    records_with_stages = [r for r in sleep_records if r.get('stages_summary')]
    
    if not records_with_stages:
        print("No sleep stage data available")
        return None
    
    records_with_stages = sorted(records_with_stages, key=lambda x: x['date_of_sleep'])
    
    dates = [r['date_of_sleep'] for r in records_with_stages]
    
    # Extract stage data
    deep = [r['stages_summary']['deep'] for r in records_with_stages]
    light = [r['stages_summary']['light'] for r in records_with_stages]
    rem = [r['stages_summary']['rem'] for r in records_with_stages]
    wake = [r['stages_summary']['wake'] for r in records_with_stages]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(dates))
    width = 0.7
    
    # Create stacked bars
    ax.bar(x, deep, width, label='Deep', color=SLEEP_COLORS['deep'])
    ax.bar(x, light, width, bottom=deep, label='Light', color=SLEEP_COLORS['light'])
    ax.bar(x, rem, width, bottom=[d+l for d,l in zip(deep, light)], label='REM', color=SLEEP_COLORS['rem'])
    ax.bar(x, wake, width, bottom=[d+l+r for d,l,r in zip(deep, light, rem)], label='Wake', color=SLEEP_COLORS['wake'])
    
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=45, ha='right')
    ax.set_xlabel('Date')
    ax.set_ylabel('Minutes')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    return fig


def create_all_charts(sleep_records, output_dir=".", single_color=None, start_date=None, end_date=None):
    """
    Create all available charts for the sleep data.
    
    Args:
        sleep_records: List of parsed sleep records
        output_dir: Directory to save charts
        single_color: Optional color to use for all sleep periods in the sleep chart
        start_date: Optional start date string (YYYY-MM-DD) for the date range
        end_date: Optional end date string (YYYY-MM-DD) for the date range
    
    Returns:
        List of figure objects
    """
    figures = []
    
    # Sleep periods chart
    fig1 = create_sleep_chart(
        sleep_records,
        title="Sleep Periods by Day",
        save_path=f"{output_dir}/sleep_periods.png",
        single_color=single_color,
        start_date=start_date,
        end_date=end_date
    )
    if fig1:
        figures.append(fig1)
    
    # Duration chart
    fig2 = create_sleep_duration_chart(
        sleep_records,
        title="Sleep Duration Over Time",
        save_path=f"{output_dir}/sleep_duration.png"
    )
    if fig2:
        figures.append(fig2)
    
    # Stages summary (if available)
    fig3 = create_sleep_stages_summary(
        sleep_records,
        title="Sleep Stages Distribution",
        save_path=f"{output_dir}/sleep_stages.png"
    )
    if fig3:
        figures.append(fig3)
    
    return figures


if __name__ == "__main__":
    # Demo with sample data
    sample_records = [
        {
            'date_of_sleep': '2026-01-20',
            'start_time': '2026-01-19T23:30:00',
            'end_time': '2026-01-20T07:15:00',
            'duration_hours': 7.75,
            'is_main_sleep': True,
            'stages_summary': {'deep': 90, 'light': 240, 'rem': 100, 'wake': 35}
        },
        {
            'date_of_sleep': '2026-01-21',
            'start_time': '2026-01-20T22:45:00',
            'end_time': '2026-01-21T06:30:00',
            'duration_hours': 7.75,
            'is_main_sleep': True,
            'stages_summary': {'deep': 85, 'light': 250, 'rem': 95, 'wake': 40}
        },
        {
            'date_of_sleep': '2026-01-22',
            'start_time': '2026-01-22T00:15:00',
            'end_time': '2026-01-22T08:00:00',
            'duration_hours': 7.75,
            'is_main_sleep': True,
            'stages_summary': {'deep': 95, 'light': 230, 'rem': 110, 'wake': 30}
        },
    ]
    
    print("Creating demo charts with sample data...")
    create_all_charts(sample_records)
    plt.show()
