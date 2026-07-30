"""由分析程式名稱建立精簡 analysis key，並保留可辨識的日期時間前綴。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


# 優先處理完整片語，避免逐字縮寫後失去原本的專業語意。
PHRASE_ABBREVIATIONS = {
    ("sea", "surface", "temperature", "anomaly"): "ssta",
    ("sea", "surface", "temperature"): "sst",
    ("root", "mean", "square", "error"): "rmse",
    ("probability", "of", "detection"): "pod",
    ("false", "alarm", "ratio"): "far",
    ("critical", "success", "index"): "csi",
    ("equitable", "threat", "score"): "ets",
    ("kling", "gupta", "efficiency"): "kge",
    ("multiple", "linear", "regression"): "mlreg",
    ("rainfall", "intensity"): "rainint",
    ("accumulated", "rainfall"): "acc_rain",
    ("rainfall", "difference"): "rain_diff",
    ("region", "mean"): "rmean",
    ("regional", "mean"): "rmean",
    ("region", "statistics"): "rstats",
    ("regional", "statistics"): "rstats",
    ("spatial", "mean"): "spmean",
    ("ensemble", "mean"): "ensmean",
    ("all", "members"): "allmem",
    ("time", "average"): "tavg",
    ("time", "averaged"): "tavg",
    ("time", "mean"): "tmean",
    ("time", "series"): "ts",
    ("running", "mean"): "runmean",
    ("moving", "average"): "movavg",
    ("cross", "section"): "xsec",
    ("linear", "trend"): "lintrend",
    ("linear", "regression"): "linreg",
    ("standard", "deviation"): "stddev",
    ("latitude", "weighted"): "latwgt",
    ("sea", "level", "pressure"): "slp",
    ("relative", "humidity"): "rh",
    ("specific", "humidity"): "sphum",
    ("potential", "temperature"): "pottemp",
    ("geopotential", "height"): "ghgt",
    ("wind", "speed"): "wspd",
    ("wind", "direction"): "wdir",
    ("mean", "absolute", "error"): "mae",
}

# 僅縮寫跨分析程式仍容易辨識的常見單詞。
WORD_ABBREVIATIONS = {
    "accumulated": "acc",
    "accumulation": "acc",
    "analysis": "ana",
    "annual": "ann",
    "anomaly": "anom",
    "average": "avg",
    "averaged": "avg",
    "climatology": "clim",
    "comparison": "comp",
    "composite": "compo",
    "control": "ctl",
    "correlation": "corr",
    "daily": "day",
    "difference": "diff",
    "distribution": "dist",
    "duration": "dur",
    "ensemble": "ens",
    "environment": "env",
    "environmental": "env",
    "experiment": "exp",
    "forecast": "fcst",
    "frequency": "freq",
    "horizontal": "horiz",
    "intensity": "int",
    "latitude": "lat",
    "latitudinal": "lat",
    "longitude": "lon",
    "longitudinal": "lon",
    "maximum": "max",
    "member": "mem",
    "members": "mem",
    "meridional": "merid",
    "minimum": "min",
    "monthly": "mon",
    "observation": "obs",
    "observational": "obs",
    "observed": "obs",
    "percentile": "pct",
    "plotter": "plot",
    "precipitation": "prcp",
    "pressure": "pres",
    "probability": "prob",
    "quantile": "qtile",
    "rainfall": "rain",
    "region": "rgn",
    "regional": "rgnl",
    "regression": "regress",
    "sensitivity": "sens",
    "significance": "sig",
    "simulation": "sim",
    "statistics": "stats",
    "statistical": "stat",
    "surface": "sfc",
    "temperature": "temp",
    "threshold": "thres",
    "time": "t",
    "vertical": "vert",
    "versus": "vs",
    "weighted": "wgt",
    "yearly": "yr",
}

# 省略後不會改變分析主題的英文連接詞。
OMITTED_WORDS = frozenset({"among", "by", "for", "of", "the", "with"})

_DATE_TOKEN_FORMATS = {
    6: "%y%m%d",
    8: "%Y%m%d",
}
_TIME_TOKEN_RE = re.compile(r"^(?:[01]\d|2[0-3])[0-5]\d(?:[0-5]\d)?$")
_DATETIME_TOKEN_RE = re.compile(
    r"^(?P<date>\d{6}|\d{8})[-T](?P<time>\d{4}|\d{6})$"
)
_PHRASE_LENGTHS = tuple(
    sorted({len(phrase) for phrase in PHRASE_ABBREVIATIONS}, reverse=True)
)


def _is_date_token(token):
    """確認字串是否為有效的 YYMMDD 或 YYYYMMDD 日期。"""
    date_format = _DATE_TOKEN_FORMATS.get(len(token))
    if date_format is None or not token.isdigit():
        return False
    try:
        datetime.strptime(token, date_format)
    except ValueError:
        return False
    return True


def _is_time_token(token):
    """確認字串是否為有效的 HHMM 或 HHMMSS 時間。"""
    return _TIME_TOKEN_RE.fullmatch(token) is not None


def _is_datetime_token(token):
    """確認單一字串是否包含有效的日期與時間。"""
    matched = _DATETIME_TOKEN_RE.fullmatch(token)
    if matched is None:
        return False
    return (
        _is_date_token(matched.group("date"))
        and _is_time_token(matched.group("time"))
    )


def _find_suffix_start(tokens):
    """找出日期及可選時間結束後，分析名稱語意區段的起始位置。"""
    for index, token in enumerate(tokens):
        if _is_datetime_token(token):
            return index + 1
        if not _is_date_token(token):
            continue

        suffix_start = index + 1
        if (
            suffix_start < len(tokens)
            and _is_time_token(tokens[suffix_start])
        ):
            suffix_start += 1
        return suffix_start
    return None


def _abbreviate_suffix(tokens):
    """依片語、單詞及省略詞規則縮寫分析名稱的語意區段。"""
    abbreviated_tokens = []
    token_index = 0

    while token_index < len(tokens):
        phrase_matched = False
        for phrase_length in _PHRASE_LENGTHS:
            phrase_end = token_index + phrase_length
            if phrase_end > len(tokens):
                continue

            phrase = tuple(
                token.lower()
                for token in tokens[token_index:phrase_end]
            )
            abbreviation = PHRASE_ABBREVIATIONS.get(phrase)
            if abbreviation is None:
                continue

            abbreviated_tokens.append(abbreviation)
            token_index = phrase_end
            phrase_matched = True
            break

        if phrase_matched:
            continue

        token = tokens[token_index]
        normalized_token = token.lower()
        if normalized_token not in OMITTED_WORDS:
            abbreviated_tokens.append(
                WORD_ABBREVIATIONS.get(normalized_token, token)
            )
        token_index += 1

    return abbreviated_tokens


def make_analysis_key(script_name):
    """保留程式日期時間前綴，縮寫其後語意並回傳 analysis key。

    有合法 YYMMDD 或 YYYYMMDD 日期時，只縮寫日期及可選時間後的語意；
    沒有合法日期時，縮寫完整名稱。分析程式應以
    ``make_analysis_key(SCRIPT_NAME)`` 建立輸出目錄專名，同時保留原本
    ``SCRIPT_NAME`` 供標題、紀錄及其他程式識別用途。
    """
    script_stem = Path(str(script_name)).stem
    if not script_stem:
        raise ValueError("script_name must not be empty.")

    tokens = script_stem.split("_")
    suffix_start = _find_suffix_start(tokens)
    if suffix_start is None:
        suffix_start = 0
    elif suffix_start >= len(tokens):
        return script_stem

    prefix_tokens = tokens[:suffix_start]
    suffix_tokens = _abbreviate_suffix(tokens[suffix_start:])
    if not suffix_tokens:
        return "_".join(prefix_tokens) or script_stem
    return "_".join([*prefix_tokens, *suffix_tokens])


__all__ = ["make_analysis_key"]
