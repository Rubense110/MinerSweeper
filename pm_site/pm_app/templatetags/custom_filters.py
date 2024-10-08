from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_duration(value):
    """Función para formatear el tiempo en timedelta a algo legible"""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    return value

@register.filter
def calculate_id(solution_id, execution_id):
    return solution_id - (10 * (execution_id - 1))