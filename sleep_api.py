"""
Fitbit Sleep API Module
Handles retrieving sleep data from the Fitbit API.
"""

import requests
from datetime import datetime, timedelta
from config import API_BASE_URL


class FitbitSleepAPI:
    """Class to interact with Fitbit Sleep API."""
    
    def __init__(self, access_token):
        """Initialize with access token."""
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    
    def get_sleep_log_by_date(self, date):
        """
        Get sleep log for a specific date.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
        
        Returns:
            Sleep log data as dictionary
        """
        url = f"{API_BASE_URL}/1.2/user/-/sleep/date/{date}.json"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_sleep_log_range(self, start_date, end_date):
        """
        Get sleep logs for a date range.
        
        Args:
            start_date: Start date string in format 'YYYY-MM-DD'
            end_date: End date string in format 'YYYY-MM-DD'
        
        Returns:
            Sleep log data as dictionary
        """
        url = f"{API_BASE_URL}/1.2/user/-/sleep/date/{start_date}/{end_date}.json"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_sleep_log_list(self, before_date=None, after_date=None, sort='desc', limit=100):
        """
        Get a list of sleep logs.
        
        Args:
            before_date: Get logs before this date (YYYY-MM-DD)
            after_date: Get logs after this date (YYYY-MM-DD)
            sort: Sort order ('asc' or 'desc')
            limit: Maximum number of entries (max 100)
        
        Returns:
            Sleep log list data as dictionary
        """
        if before_date:
            url = f"{API_BASE_URL}/1.2/user/-/sleep/list.json?beforeDate={before_date}&sort={sort}&offset=0&limit={limit}"
        elif after_date:
            url = f"{API_BASE_URL}/1.2/user/-/sleep/list.json?afterDate={after_date}&sort={sort}&offset=0&limit={limit}"
        else:
            # Default to getting recent sleep logs
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{API_BASE_URL}/1.2/user/-/sleep/list.json?beforeDate={today}&sort={sort}&offset=0&limit={limit}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_sleep_log_range_chunked(self, start_date, end_date, max_days_per_request=100):
        """
        Get sleep logs for a date range, handling ranges > 100 days by making multiple requests.
        
        Args:
            start_date: Start date string in format 'YYYY-MM-DD'
            end_date: End date string in format 'YYYY-MM-DD'
            max_days_per_request: Maximum days per API request (default 100)
        
        Returns:
            Sleep log data as dictionary with combined results
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        total_days = (end_dt - start_dt).days
        
        # If within limit, make a single request
        if total_days <= max_days_per_request:
            return self.get_sleep_log_range(start_date, end_date)
        
        # Otherwise, make multiple requests and combine results
        all_sleep_records = []
        current_start = start_dt
        request_count = 0
        
        print(f"Retrieving {total_days} days of data in multiple requests...")
        
        while current_start < end_dt:
            # Calculate chunk end date (max 100 days from current start)
            chunk_end = min(current_start + timedelta(days=max_days_per_request), end_dt)
            
            chunk_start_str = current_start.strftime('%Y-%m-%d')
            chunk_end_str = chunk_end.strftime('%Y-%m-%d')
            
            request_count += 1
            print(f"  Request {request_count}: {chunk_start_str} to {chunk_end_str}")
            
            # Make API request for this chunk
            chunk_data = self.get_sleep_log_range(chunk_start_str, chunk_end_str)
            
            # Add sleep records from this chunk
            if 'sleep' in chunk_data:
                all_sleep_records.extend(chunk_data['sleep'])
            
            # Move to next chunk (start from day after chunk_end to avoid overlap)
            current_start = chunk_end + timedelta(days=1)
        
        print(f"  Retrieved {len(all_sleep_records)} total sleep records")
        
        # Return combined data in same format as single request
        return {'sleep': all_sleep_records}
    
    def get_recent_sleep_logs(self, days=30):
        """
        Get sleep logs for the recent specified number of days.
        Automatically handles requests for more than 100 days.
        
        Args:
            days: Number of days to retrieve (default 30)
        
        Returns:
            Sleep log data as dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_sleep_log_range_chunked(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )


def parse_sleep_data(sleep_response):
    """
    Parse sleep data from API response into a structured format.
    
    Args:
        sleep_response: Raw API response dictionary
    
    Returns:
        List of dictionaries with parsed sleep information
    """
    sleep_records = []
    
    # Handle both single date and range responses
    sleep_list = sleep_response.get('sleep', [])
    
    for sleep in sleep_list:
        record = {
            'log_id': sleep.get('logId'),
            'date_of_sleep': sleep.get('dateOfSleep'),
            'start_time': sleep.get('startTime'),
            'end_time': sleep.get('endTime'),
            'duration_ms': sleep.get('duration'),
            'duration_hours': sleep.get('duration', 0) / (1000 * 60 * 60),
            'efficiency': sleep.get('efficiency'),
            'is_main_sleep': sleep.get('isMainSleep'),
            'minutes_asleep': sleep.get('minutesAsleep'),
            'minutes_awake': sleep.get('minutesAwake'),
            'time_in_bed': sleep.get('timeInBed'),
            'type': sleep.get('type'),  # 'classic' or 'stages'
        }
        
        # Parse sleep stages if available (for 'stages' type)
        if sleep.get('levels'):
            levels = sleep['levels']
            
            # Get summary data
            summary = levels.get('summary', {})
            record['stages_summary'] = {
                'deep': summary.get('deep', {}).get('minutes', 0),
                'light': summary.get('light', {}).get('minutes', 0),
                'rem': summary.get('rem', {}).get('minutes', 0),
                'wake': summary.get('wake', {}).get('minutes', 0),
            }
            
            # Get detailed level data (for visualization)
            record['levels_data'] = levels.get('data', [])
            record['short_data'] = levels.get('shortData', [])
        
        sleep_records.append(record)
    
    return sleep_records


if __name__ == "__main__":
    # Test the API (requires valid token)
    from fitbit_auth import authenticate
    
    token = authenticate()
    if token:
        api = FitbitSleepAPI(token)
        
        # Get recent sleep data
        try:
            data = api.get_recent_sleep_logs(days=7)
            records = parse_sleep_data(data)
            
            print(f"\nFound {len(records)} sleep records:")
            for record in records:
                print(f"  {record['date_of_sleep']}: {record['duration_hours']:.1f} hours")
        except Exception as e:
            print(f"Error: {e}")
