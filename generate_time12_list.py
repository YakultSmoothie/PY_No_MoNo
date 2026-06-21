#!/usr/bin/env python3
"""
Generate a list of time codes with minute precision.

Supported output formats:
- time12: yyyymmddhhmm (default)
- wrf: yyyy-mm-dd_hh:mm:00
- iso: yyyy-mm-ddThh:mm

create: 2026-06-15 (v1.0)
"""
#===============================================================================
from datetime import datetime, timedelta
import sys


def generate_time_codes(start_time: str, end_time: str, interval: int, output_format: str = 'time12'):
    """
    Generate time codes between start_time and end_time, inclusive.

    Args:
        start_time: Start time in YYYYMMDDHHMM format.
        end_time: End time in YYYYMMDDHHMM format.
        interval: Time interval in minutes.
        output_format: Output format ('time12', 'wrf', or 'iso').

    Returns:
        A list of formatted time strings.
    """
    if interval <= 0:
        raise ValueError("interval_minutes must be a positive integer")

    start_dt = datetime.strptime(start_time, "%Y%m%d%H%M")
    end_dt = datetime.strptime(end_time, "%Y%m%d%H%M")
    step = timedelta(minutes=interval)
    if start_dt > end_dt:
        step = -step

    times = []
    current_dt = start_dt

    while (step > timedelta(0) and current_dt <= end_dt) or (step < timedelta(0) and current_dt >= end_dt):
        if output_format == 'time12':
            times.append(current_dt.strftime("%Y%m%d%H%M"))
        elif output_format == 'wrf':
            times.append(current_dt.strftime("%Y-%m-%d_%H:%M:00"))
        elif output_format == 'iso':
            times.append(current_dt.strftime("%Y-%m-%dT%H:%M"))
        else:
            raise ValueError(f"Unsupported output format: {output_format} [at def generate_time_codes]")
        current_dt += step

    return times


def main():
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: generate_time12_list.py <start_time> <end_time> <interval_minutes> [separator] [format]")
        print("Arguments:")
        print("  start_time: Start time in YYYYMMDDHHMM format, example: 202507300100")
        print("  end_time: End time in YYYYMMDDHHMM format, example: 202507300130")
        print("  interval_minutes: Time interval in minutes")
        print("  separator: Optional separator, default is comma")
        print("  format: Optional output format, default is time12")
        print("    - time12: YYYYMMDDHHMM")
        print("    - wrf: YYYY-MM-DD_HH:MM:00")
        print("    - iso: YYYY-MM-DDTHH:MM")
        print()
        print("Examples:")
        print("  generate_time12_list.py 202507300100 202507300130 10")
        print("    -> 202507300100,202507300110,202507300120,202507300130")
        print("  generate_time12_list.py 202507300100 202507300130 10 ' ' wrf")
        print("    -> 2025-07-30_01:00:00 2025-07-30_01:10:00 2025-07-30_01:20:00 2025-07-30_01:30:00")
        print("  generate_time12_list.py 202507300100 202507300130 10 ',' iso")
        print("    -> 2025-07-30T01:00,2025-07-30T01:10,2025-07-30T01:20,2025-07-30T01:30")
        sys.exit(1)

    start_time = sys.argv[1]
    end_time = sys.argv[2]
    interval = int(sys.argv[3])

    if len(sys.argv) >= 5:
        separator = sys.argv[4]
        if separator == '\\n':
            separator = '\n'
        elif separator == '\\t':
            separator = '\t'
    else:
        separator = ','

    if len(sys.argv) >= 6:
        output_format = sys.argv[5].lower()
        if output_format not in ['time12', 'wrf', 'iso']:
            print(f"Error: Unsupported output format '{output_format}'")
            print("Supported formats: time12, wrf, iso")
            sys.exit(1)
    else:
        output_format = 'time12'

    try:
        result = generate_time_codes(start_time, end_time, interval, output_format)
        print(separator.join(result))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
#===============================================================================

"""
Examples:

1. Default output, comma-separated:
   Command:
     generate_time12_list.py 202507300100 202507300130 10

   Output:
     202507300100,202507300110,202507300120,202507300130

2. Space-separated output:
   Command:
     generate_time12_list.py 202507300100 202507300130 10 ' '

   Output:
     202507300100 202507300110 202507300120 202507300130

3. WRF output:
   Command:
     generate_time12_list.py 202507300100 202507300130 10 ',' wrf

   Output:
     2025-07-30_01:00:00,2025-07-30_01:10:00,2025-07-30_01:20:00,2025-07-30_01:30:00

4. ISO output:
   Command:
     generate_time12_list.py 202507300100 202507300130 10 ',' iso

   Output:
     2025-07-30T01:00,2025-07-30T01:10,2025-07-30T01:20,2025-07-30T01:30

5. Newline-separated output:
   Command:
     generate_time12_list.py 202507300100 202507300130 10 '\\n'

   Output:
     202507300100
     202507300110
     202507300120
     202507300130

6. Reverse output:
   Command:
     generate_time12_list.py 202507300130 202507300100 10

   Output:
     202507300130,202507300120,202507300110,202507300100
"""
