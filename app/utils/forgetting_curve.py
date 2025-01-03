from datetime import datetime, timedelta

def calculate_review_words(start_date, days):
    """计算需要复习的日期
    Args:
        start_date: 开始学习的日期
        days: 学习天数
    Returns:
        list: 需要复习的日期列表
    """
    review_intervals = [1, 2, 4, 7, 15, 30]  # 复习间隔天数
    review_dates = []

    for interval in review_intervals:
        review_date = start_date + timedelta(days=interval)
        if (review_date - start_date).days <= days:
            review_dates.append(review_date)

    return review_dates 