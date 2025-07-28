"""
Date utility functions for the LangGraph assistant.
"""

from datetime import datetime, timedelta
import re
from typing import Optional

def parse_relative_date(date_text: str) -> str:
    """
    Parse relative date expressions and convert to YYYY-MM-DD format.
    
    Args:
        date_text (str): Date expression like "tomorrow", "next week", "July 22", etc.
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    current_date = datetime.now()
    date_text = date_text.lower().strip()
    
    # Handle "tomorrow"
    if date_text == "tomorrow":
        tomorrow = current_date + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    # Handle "today"
    if date_text == "today":
        return current_date.strftime('%Y-%m-%d')
    
    # Handle "next week"
    if date_text == "next week":
        next_week = current_date + timedelta(days=7)
        return next_week.strftime('%Y-%m-%d')
    
    # Handle "next month"
    if date_text == "next month":
        # Simple next month calculation
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1)
        return next_month.strftime('%Y-%m-%d')
    
    # Handle "in X days"
    match = re.match(r'in (\d+) days?', date_text)
    if match:
        days = int(match.group(1))
        future_date = current_date + timedelta(days=days)
        return future_date.strftime('%Y-%m-%d')
    
    # Handle "X days from now"
    match = re.match(r'(\d+) days? from now', date_text)
    if match:
        days = int(match.group(1))
        future_date = current_date + timedelta(days=days)
        return future_date.strftime('%Y-%m-%d')
    
    # Handle month names with day (e.g., "July 22", "Dec 15")
    month_patterns = [
        r'(january|jan)\s+(\d{1,2})',
        r'(february|feb)\s+(\d{1,2})',
        r'(march|mar)\s+(\d{1,2})',
        r'(april|apr)\s+(\d{1,2})',
        r'(may)\s+(\d{1,2})',
        r'(june|jun)\s+(\d{1,2})',
        r'(july|jul)\s+(\d{1,2})',
        r'(august|aug)\s+(\d{1,2})',
        r'(september|sept|sep)\s+(\d{1,2})',
        r'(october|oct)\s+(\d{1,2})',
        r'(november|nov)\s+(\d{1,2})',
        r'(december|dec)\s+(\d{1,2})'
    ]
    
    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    
    for i, pattern in enumerate(month_patterns):
        match = re.match(pattern, date_text)
        if match:
            month = i + 1  # 1-based month
            day = int(match.group(2))
            
            # Assume current year unless the date has already passed
            year = current_date.year
            try:
                test_date = datetime(year, month, day)
                if test_date < current_date:
                    # If the date has passed this year, assume next year
                    year += 1
            except ValueError:
                # Invalid date, return current date
                return current_date.strftime('%Y-%m-%d')
            
            return f"{year}-{month:02d}-{day:02d}"
    
    # Handle MM/DD or MM-DD format
    match = re.match(r'(\d{1,2})[/-](\d{1,2})', date_text)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        
        # Assume current year unless the date has already passed
        year = current_date.year
        try:
            test_date = datetime(year, month, day)
            if test_date < current_date:
                # If the date has passed this year, assume next year
                year += 1
        except ValueError:
            # Invalid date, return current date
            return current_date.strftime('%Y-%m-%d')
        
        return f"{year}-{month:02d}-{day:02d}"
    
    # If no pattern matches, return current date
    return current_date.strftime('%Y-%m-%d')

def format_date_for_flights(date_text: str) -> str:
    """
    Format date text for flight searches, ensuring YYYY-MM-DD format.
    
    Args:
        date_text (str): Date text from user input
        
    Returns:
        str: Properly formatted date for flight API
    """
    # If it's already in YYYY-MM-DD format, return as is
    if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
        return date_text
    
    # Otherwise, parse it
    return parse_relative_date(date_text)

def get_current_date_context() -> dict:
    """
    Get current date context for system prompts.
    
    Returns:
        dict: Current date information
    """
    current_date = datetime.now()
    return {
        "current_date": current_date.strftime('%Y-%m-%d'),
        "current_year": current_date.year,
        "current_month": current_date.month,
        "current_day": current_date.day,
        "tomorrow": (current_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        "next_week": (current_date + timedelta(days=7)).strftime('%Y-%m-%d')
    } 