#!/bin/bash
path_to_file=$1
open_companion=$2
if [ $open_companion -eq 1 ]; then
    gnuradio-companion $path_to_file
else
    grcc -r $path_to_file
fi