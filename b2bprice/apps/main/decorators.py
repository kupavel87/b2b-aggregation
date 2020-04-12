from datetime import datetime


def duration_time(func):
    def wrap(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        duration = f"\tВремя запроса: {datetime.now() - start}"
        result['text'] = result.get('text', 'Error') + duration
        return result
    return wrap
