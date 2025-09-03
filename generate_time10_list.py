from datetime import datetime, timedelta

def generate_time10_list(start_time: str, end_time: str, interval: int):
    """
    產生時間(十碼時間）代碼序列 (yyyymmddhh)

    Parameters
    ----------
    start_time : str
        開始時間 (10 碼, yyyymmddhh)
    end_time : str
        結束時間 (10 碼, yyyymmddhh)
    interval : int
        間隔 (小時)

    Returns
    -------
    list of str
        時間代碼列表
    """
    # 轉換成 datetime
    start_dt = datetime.strptime(start_time, "%Y%m%d%H")
    end_dt = datetime.strptime(end_time, "%Y%m%d%H")

    # 生成序列
    times = []
    current_dt = start_dt
    while current_dt <= end_dt:
        times.append(current_dt.strftime("%Y%m%d%H"))
        current_dt += timedelta(hours=interval)

    return times


# 測試
# print(generate_time10_list("2025073001", "2025073003", 1))
