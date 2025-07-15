def datetime_to_grads_time(dt):
    """
    將 datetime 物件轉換為 GrADS 時間格式 (例如: 06Z09JUN2006)
    """
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    hour = dt.hour
    day = dt.day
    month = month_names[dt.month - 1]
    year = dt.year
    
    return f"{hour:02d}Z{day:02d}{month}{year}"
