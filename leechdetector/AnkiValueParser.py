import time

def is_failed(review) -> bool:
    # Check if the review was a failure
    return review.button_chosen == 1

def is_success(review) -> bool:
    return is_actual_review(review) and not is_failed(review)

def is_actual_review(review) -> bool:
    return review.button_chosen > 0

def time_to_date(time_epoch: int) -> str:
    # Convert the time to a human-readable date format
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time_epoch))

def interval_to_duration_display(interval: int) -> str:
    # Convert the interval to a human-readable format
    days = interval / 60 / 60 / 24
    if days > 30:
        return f"{days / 30:.2f} months"
    else:
        return f"{int(days)} days"

def interval_to_days(interval : int) -> int:
    return int(interval / 60 / 60 / 24)

def time_to_days(time_epoch: int) -> int:
    # Convert the time to a human-readable date format
    return int(time_epoch / 60 / 60 / 24)

