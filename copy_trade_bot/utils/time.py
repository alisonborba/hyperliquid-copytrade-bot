"""
Time utilities for the CopyTrade bot.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Union


def get_current_timestamp() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds
    """
    return int(time.time() * 1000)


def get_current_datetime() -> datetime:
    """
    Get current datetime in UTC.
    
    Returns:
        Current datetime in UTC
    """
    return datetime.now(timezone.utc)


def parse_timestamp(timestamp: Union[int, float, str]) -> datetime:
    """
    Parse timestamp to datetime.
    
    Args:
        timestamp: Timestamp (seconds or milliseconds)
        
    Returns:
        Parsed datetime
    """
    if isinstance(timestamp, str):
        timestamp = float(timestamp)
    
    # If timestamp is in milliseconds, convert to seconds
    if timestamp > 1e10:  # Likely milliseconds
        timestamp = timestamp / 1000
    
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def format_timestamp(timestamp: Union[int, float, datetime]) -> str:
    """
    Format timestamp to ISO string.
    
    Args:
        timestamp: Timestamp or datetime
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, (int, float)):
        dt = parse_timestamp(timestamp)
    else:
        dt = timestamp
    
    return dt.isoformat()


def is_timestamp_recent(timestamp: Union[int, float, datetime], max_age_seconds: int = 60) -> bool:
    """
    Check if timestamp is recent (within max_age_seconds).
    
    Args:
        timestamp: Timestamp to check
        max_age_seconds: Maximum age in seconds
        
    Returns:
        True if timestamp is recent, False otherwise
    """
    if isinstance(timestamp, datetime):
        dt = timestamp
    else:
        dt = parse_timestamp(timestamp)
    
    now = get_current_datetime()
    age = (now - dt).total_seconds()
    
    return age <= max_age_seconds


def get_time_difference(
    timestamp1: Union[int, float, datetime],
    timestamp2: Union[int, float, datetime]
) -> float:
    """
    Get time difference between two timestamps in seconds.
    
    Args:
        timestamp1: First timestamp
        timestamp2: Second timestamp
        
    Returns:
        Time difference in seconds
    """
    if isinstance(timestamp1, (int, float)):
        dt1 = parse_timestamp(timestamp1)
    else:
        dt1 = timestamp1
    
    if isinstance(timestamp2, (int, float)):
        dt2 = parse_timestamp(timestamp2)
    else:
        dt2 = timestamp2
    
    return abs((dt1 - dt2).total_seconds())


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_market_hours() -> tuple[datetime, datetime]:
    """
    Get current market hours (24/7 for crypto).
    
    Returns:
        Tuple of (market_open, market_close) datetimes
    """
    now = get_current_datetime()
    market_open = now.replace(hour=0, minute=0, second=0, microsecond=0)
    market_close = market_open.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return market_open, market_close


def is_market_open() -> bool:
    """
    Check if market is currently open (always true for crypto).
    
    Returns:
        True (crypto markets are always open)
    """
    return True


def get_trading_day_start() -> datetime:
    """
    Get the start of the current trading day (UTC midnight).
    
    Returns:
        Start of current trading day
    """
    now = get_current_datetime()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_trading_day_end() -> datetime:
    """
    Get the end of the current trading day (UTC midnight).
    
    Returns:
        End of current trading day
    """
    now = get_current_datetime()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)


def is_same_trading_day(timestamp1: Union[int, float, datetime], timestamp2: Union[int, float, datetime]) -> bool:
    """
    Check if two timestamps are on the same trading day.
    
    Args:
        timestamp1: First timestamp
        timestamp2: Second timestamp
        
    Returns:
        True if timestamps are on the same trading day
    """
    if isinstance(timestamp1, (int, float)):
        dt1 = parse_timestamp(timestamp1)
    else:
        dt1 = timestamp1
    
    if isinstance(timestamp2, (int, float)):
        dt2 = parse_timestamp(timestamp2)
    else:
        dt2 = timestamp2
    
    return dt1.date() == dt2.date()


def get_week_start(timestamp: Optional[Union[int, float, datetime]] = None) -> datetime:
    """
    Get the start of the week (Monday) for a given timestamp.
    
    Args:
        timestamp: Timestamp (defaults to current time)
        
    Returns:
        Start of the week
    """
    if timestamp is None:
        dt = get_current_datetime()
    elif isinstance(timestamp, (int, float)):
        dt = parse_timestamp(timestamp)
    else:
        dt = timestamp
    
    # Get Monday of the current week
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_month_start(timestamp: Optional[Union[int, float, datetime]] = None) -> datetime:
    """
    Get the start of the month for a given timestamp.
    
    Args:
        timestamp: Timestamp (defaults to current time)
        
    Returns:
        Start of the month
    """
    if timestamp is None:
        dt = get_current_datetime()
    elif isinstance(timestamp, (int, float)):
        dt = parse_timestamp(timestamp)
    else:
        dt = timestamp
    
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def sleep_until(target_time: Union[int, float, datetime]) -> None:
    """
    Sleep until a target time.
    
    Args:
        target_time: Target time to sleep until
    """
    if isinstance(target_time, (int, float)):
        target_dt = parse_timestamp(target_time)
    else:
        target_dt = target_time
    
    now = get_current_datetime()
    if target_dt > now:
        sleep_seconds = (target_dt - now).total_seconds()
        time.sleep(sleep_seconds)
