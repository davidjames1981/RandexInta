from django import template

register = template.Library()

@register.filter
def get_range(total_pages, current_page):
    """
    Generate a range of page numbers for pagination.
    Shows current page and adjacent pages, with ellipsis for gaps.
    """
    current_page = int(current_page)
    total_pages = int(total_pages)
    
    # Always include first and last pages
    page_range = set([1, total_pages])
    
    # Add current page and adjacent pages
    for page in range(max(1, current_page - 1), min(total_pages + 1, current_page + 2)):
        page_range.add(page)
    
    # Convert to sorted list
    return sorted(list(page_range))

@register.filter
def range_filter(value):
    """Returns a range of numbers from 1 to value (inclusive)"""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return [] 