"""顯示 Python 互動環境的輸入歷史。"""

import readline


__all__ = ["history"]


def history(n=None):
    """
    顯示 Python 互動環境的輸入歷史。

    Parameters
    ----------
    n : int, str or None, default=None
        傳入整數時顯示最近幾筆輸入；傳入字串時顯示包含該字串的
        歷史命令；設為 ``None`` 時顯示全部歷史。

    Returns
    -------
    None
        歷史內容會直接輸出至終端。
    """
    if isinstance(n, bool) or (
        n is not None and not isinstance(n, (int, str))
    ):
        raise TypeError("n 必須是正整數、搜尋字串或 None。")
    if isinstance(n, int) and n <= 0:
        raise ValueError("n 為整數時必須大於 0。")
    if isinstance(n, str) and not n:
        raise ValueError("搜尋字串不可為空字串。")

    # 取得歷史總數，並依整數筆數決定開始顯示的位置。
    total = readline.get_current_history_length()
    start = max(1, total - n + 1) if isinstance(n, int) else 1

    for index in range(start, total + 1):
        command = readline.get_history_item(index)
        if isinstance(n, str) and (command is None or n not in command):
            continue
        print(f"{index}: {command}")
