#!/bin/bash
ssh $1 "-p$2" request $3 |
    tee data.in.tmp >(sed 's/^/< /' 1>&2) |
    ${@:4} |
    tee data.out.tmp >(sed 's/^/> /' 1>&2) |
    ssh $1 "-p$2" submit $3
