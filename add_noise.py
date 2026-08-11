#!/usr/bin/env python3
#----------------------
# add_noise.py
#----------------------
# v1.0 - YakultSmoothie - 2024.08.08

# ============================================================================================
import random
import sys

def add_gaussian_noise(number: float, std_dev: float) -> float:
    noise = random.gauss(0, std_dev)
    return number + noise

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python add_noise.py <standard deviation> <value>")
    else:
        try:
            std_dev = float(sys.argv[1])
            number = float(sys.argv[2])
            result = add_gaussian_noise(number, std_dev)
            print(f"{result}")
        except ValueError:
            print("!!! error, there is on input !!!")
# ============================================================================================
