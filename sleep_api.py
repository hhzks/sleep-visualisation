"""
Google Health Sleep API Module
Handles retrieving sleep data from the Google Health API (v4).
"""

import re
import time
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from config import API_BASE_URL

# Sleep data points: the API allows at most 25 per page.
SLEEP_PAGE_SIZE = 25

# Google Health stage types -> stage names used by the charts.
STAGE_NAMES = {
    'AWAKE': 'wake',
    'LIGHT': 'light',
    'DEEP': 'deep',
    'REM': 'rem',
    'ASLEEP': 'asleep',
    'RESTLESS': 'restless',
}


class GoogleHealthSleepAPI:
    """Class to interact with the Google Health API sleep data type."""

    def __init__(self, access_token):
        """Initialize with access token."""
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

    def _get(self, url, params, max_retries=5):
        """GET with exponential backoff on 429 / 5xx responses."""
        delay = 1
        for attempt in range(max_retries + 1):
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                return response.json()

            if response.status_code in (429, 500, 503, 504) and attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue

            if 'ACCOUNT_NOT_LINKED' in response.text:
                raise Exception(
                    "Your Google account is not linked to Google Health. "
                    "Link it in the Google Health app, then try again."
                )
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

    def get_sleep_log_range(self, start_date, end_date):
        """
        Get reconciled sleep sessions that end on a date in the range.

        Args:
            start_date: Start date string in format 'YYYY-MM-DD' (inclusive)
            end_date: End date string in format 'YYYY-MM-DD' (inclusive)

        Returns:
            Dictionary {'dataPoints': [...]} with all pages combined
        """
        # The upper bound of the filter is exclusive, so add one day.
        end_exclusive = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        url = f"{API_BASE_URL}/users/me/dataTypes/sleep/dataPoints:reconcile"
        params = {
            'pageSize': SLEEP_PAGE_SIZE,
            'filter': (
                f'sleep.interval.civil_end_time >= "{start_date}" '
                f'AND sleep.interval.civil_end_time < "{end_exclusive}"'
            ),
        }

        data_points = []
        page = 0
        while True:
            page += 1
            data = self._get(url, params)
            data_points.extend(data.get('dataPoints', []))

            next_token = data.get('nextPageToken')
            if not next_token:
                break
            params['pageToken'] = next_token

        if page > 1:
            print(f"  Retrieved {len(data_points)} sleep sessions in {page} pages")

        return {'dataPoints': data_points}

    def get_recent_sleep_logs(self, days=30):
        """
        Get sleep logs for the recent specified number of days.

        Args:
            days: Number of days to retrieve (default 30)

        Returns:
            Dictionary {'dataPoints': [...]}
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.get_sleep_log_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )


def _offset_seconds(offset):
    """Convert a duration string such as '-14400s' to seconds (0 if absent)."""
    if not offset:
        return 0
    match = re.fullmatch(r'(-?\d+(?:\.\d+)?)s', offset.strip())
    return float(match.group(1)) if match else 0


def _to_local(timestamp, utc_offset):
    """
    Convert an RFC 3339 timestamp plus a UTC offset to a naive local datetime.
    The charts use wall-clock time, so the result has no time zone.
    """
    dt = date_parser.isoparse(timestamp)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None) - dt.utcoffset()
    return dt + timedelta(seconds=_offset_seconds(utc_offset))


def _segments(items, default_offset=None):
    """
    Convert Google Health stage objects to chart 'levels' segments.
    A segment without its own UTC offset uses default_offset (the session offset).
    """
    segments = []
    for item in items:
        start_offset = item.get('startUtcOffset') or default_offset
        start = _to_local(item['startTime'], start_offset)
        end = _to_local(item['endTime'], item.get('endUtcOffset') or start_offset)
        segments.append({
            'dateTime': start.isoformat(),
            'level': STAGE_NAMES.get(item.get('type'), 'unknown'),
            'seconds': int((end - start).total_seconds()),
        })
    segments.sort(key=lambda s: s['dateTime'])
    return segments


def _int(value):
    """Convert a numeric string from the API to int (None if absent)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_sleep_data(sleep_response):
    """
    Parse sleep data from a Google Health API response into the normalized
    record format used by the charts.

    Args:
        sleep_response: Dictionary {'dataPoints': [...]}

    Returns:
        List of dictionaries with parsed sleep information
    """
    sleep_records = []

    for point in sleep_response.get('dataPoints', []):
        sleep = point.get('sleep')
        if not sleep:
            continue

        interval = sleep['interval']
        start = _to_local(interval['startTime'], interval.get('startUtcOffset'))
        end = _to_local(interval['endTime'], interval.get('endUtcOffset') or interval.get('startUtcOffset'))
        duration_ms = int((end - start).total_seconds() * 1000)

        metadata = sleep.get('metadata', {})
        summary = sleep.get('summary', {})
        sleep_type = (sleep.get('type') or '').lower()  # 'classic' or 'stages'

        minutes_asleep = _int(summary.get('minutesAsleep'))
        minutes_awake = _int(summary.get('minutesAwake'))
        minutes_in_period = _int(summary.get('minutesInSleepPeriod'))

        # The API has no efficiency field. Use the Google formula:
        # minutes asleep / minutes in bed * 100.
        efficiency = None
        if minutes_asleep is not None and minutes_in_period:
            efficiency = round(minutes_asleep / minutes_in_period * 100)

        record = {
            'log_id': point.get('dataPointName') or point.get('name'),
            # Sleep is dated by the local day on which it ends.
            'date_of_sleep': end.strftime('%Y-%m-%d'),
            'start_time': start.isoformat(),
            'end_time': end.isoformat(),
            'duration_ms': duration_ms,
            'duration_hours': duration_ms / (1000 * 60 * 60),
            'efficiency': efficiency,
            'is_main_sleep': bool(metadata.get('mainSleep', metadata.get('main', False))),
            'minutes_asleep': minutes_asleep,
            'minutes_awake': minutes_awake,
            'time_in_bed': minutes_in_period,
            'type': sleep_type,
        }

        stages = sleep.get('stages', [])
        if stages:
            session_offset = interval.get('startUtcOffset')
            record['levels_data'] = _segments(stages, session_offset)
            record['short_data'] = _segments(sleep.get('shortAwakenings', []), session_offset)

        if sleep_type == 'stages':
            totals = {'deep': 0, 'light': 0, 'rem': 0, 'wake': 0}
            stage_summary = summary.get('stagesSummary', [])
            if stage_summary:
                for entry in stage_summary:
                    name = STAGE_NAMES.get(entry.get('type'))
                    if name in totals:
                        totals[name] += _int(entry.get('minutes')) or 0
            else:
                # No summary yet: add up the stage segments.
                for seg in record.get('levels_data', []):
                    if seg['level'] in totals:
                        totals[seg['level']] += seg['seconds'] // 60
            record['stages_summary'] = totals

        sleep_records.append(record)

    return sleep_records


if __name__ == "__main__":
    # Test the API (requires valid token)
    from google_auth import authenticate

    token = authenticate()
    if token:
        api = GoogleHealthSleepAPI(token)

        try:
            data = api.get_recent_sleep_logs(days=7)
            records = parse_sleep_data(data)

            print(f"\nFound {len(records)} sleep records:")
            for record in records:
                print(f"  {record['date_of_sleep']}: {record['duration_hours']:.1f} hours")
        except Exception as e:
            print(f"Error: {e}")
