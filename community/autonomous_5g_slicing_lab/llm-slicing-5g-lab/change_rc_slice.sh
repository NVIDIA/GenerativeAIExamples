#!/bin/bash

# 1 = slice 1 Ratio
# 2 = slice 2 Ratio

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

if [ -n "$1" ] &&  [ -n "$2" ]; then

  sum=$1+$2
  echo $sum
  #if [ "$sum" -gt 100 ]; then
  #  echo "The sum of both ratios must not be greater than 100"
  #  exit()
  #fi

  export SLICE1_RATIO=$1
  export SLICE2_RATIO=$2
else
  echo "You did not specify the slicing ratios, using default 80:20"
fi

./flexric/build/examples/xApp/c/ctrl/xapp_rc_slice_dynamic
