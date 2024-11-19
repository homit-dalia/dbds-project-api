from datetime import datetime, time
def object_as_dict(obj):
    return {key: (str(value) if isinstance(value, (datetime, time)) else value)
            for key, value in obj.__dict__.items()
            if not key.startswith('_') and not callable(value)}