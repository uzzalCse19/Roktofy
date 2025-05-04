from django.core.exceptions import ValidationError
from datetime import date, timedelta

def validate_future_date(value):
    if value < date.today():
        raise ValidationError("Date cannot be in the past.")

def validate_donation_interval(last_donation):  
    if last_donation:
        days_since_last = (date.today() - last_donation).days 
        if days_since_last < 90:
            raise ValidationError(f"Only {days_since_last} days passed since last donation. Minimum 90 days required.")

