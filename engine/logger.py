# logger.py

# Set to False to disable debug logs
DEBUG_ENABLED = True

def debug(*args, **kwargs):
    """Debug log. Only printed if DEBUG_ENABLED is True."""
    if DEBUG_ENABLED:
        print(*args, **kwargs)

def info(*args, **kwargs):
    """Info log. Always printed."""
    print(*args, **kwargs)

def error(*args, **kwargs):
    """Error log. Always printed."""
    print("ERROR:", *args, **kwargs)
