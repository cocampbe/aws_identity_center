def snake_to_pascal(snake_str):
    """Convert a snake_case string to PascalCase."""
    return ''.join(word.capitalize() for word in snake_str.split('_'))

def convert_dict_keys_to_pascal(obj):
    """Recursively convert dictionary keys from snake_case to PascalCase."""
    if isinstance(obj, dict):
        return {
            snake_to_pascal(key): convert_dict_keys_to_pascal(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_dict_keys_to_pascal(item) for item in obj]
    else:
        return obj

def remove_keys_from_dict(obj, keys_to_remove):
    """Recursively remove specified keys from a dictionary."""
    if isinstance(obj, dict):
        return {
            key: remove_keys_from_dict(value, keys_to_remove)
            for key, value in obj.items()
            if key not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [remove_keys_from_dict(item, keys_to_remove) for item in obj]
    else:
        return obj

def is_empty(value):
    """Check if a value is empty (None, '', [], {})."""
    return value is None or value == "" or value == [] or value == {}

def remove_keys_empty_value(obj):
    """Recursively remove keys with empty values from a dictionary."""
    if isinstance(obj, dict):
        return {
            key: remove_keys_empty_value(value)
            for key, value in obj.items()
            if not is_empty(value)
        }
    elif isinstance(obj, list):
        return [remove_keys_empty_value(item) for item in obj if not is_empty(item)]
    else:
        return obj