from django import template
import json
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='json_encode')
def json_encode(value):
    """
    Safely encode a value as JSON for use in JavaScript
    """
    try:
        # Use DjangoJSONEncoder to handle Django-specific types
        encoded = json.dumps(value, cls=DjangoJSONEncoder)
        # Mark the string as safe since we've properly encoded it
        return mark_safe(encoded)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error encoding JSON: {str(e)}, Value: {value}")
        return '{}' # Return empty object on error 