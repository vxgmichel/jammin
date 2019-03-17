#!/bin/bash
echo "request $3" |
    nc $1 $2 |
    tee data.in.tmp >(sed 's/^/< /' 1>&2) |
    ${@:4} |
    tee data.out.tmp >(sed 's/^/> /' 1>&2) |
    { echo "submit $3"; cat; } |
    nc $1 $2
