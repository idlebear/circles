#!/bin/bash

for ((i=3; i<=1000; i++))
do
    python circles.py -s $i -n 10 -r 0.35 --prefix results/circles
done
