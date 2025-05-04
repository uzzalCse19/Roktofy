from django.core.exceptions import ValidationError
import re
def validate_phone_number(value):
    if not re.match(r'^01[3-9]\d{8}$', value):
        raise ValidationError("Enter a valid Bangladeshi phone number:")
