#!/bin/bash
# a tiny bash command to combine some files with the header only in there once
# Example
awk '(NR == 1) || (FNR > 1)' 2016*.csv > fapar2016_v2.csv