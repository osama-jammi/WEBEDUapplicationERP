from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """Get a value from a dictionary using a variable key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def format_hour(value):
    """Format float hour to HH:MM"""
    try:
        hours = int(value)
        minutes = int((value - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    except (ValueError, TypeError):
        return value


@register.simple_tag
def note_status(note_value):
    """Return CSS class based on note value"""
    try:
        value = float(note_value)
        if value >= 12:
            return 'success'
        elif value >= 10:
            return 'warning'
        else:
            return 'danger'
    except (ValueError, TypeError):
        return 'secondary'
