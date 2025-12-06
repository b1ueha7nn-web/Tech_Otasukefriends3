from datetime import datetime

def diff_hour(published_at):
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    now = datetime.now()
    delta = now - datetime.strptime(published_at, time_format)
    total_seconds = delta.total_seconds()
    hours = total_seconds // 3600

    return int(hours)

