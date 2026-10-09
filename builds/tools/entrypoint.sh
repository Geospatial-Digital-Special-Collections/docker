#!/bin/sh

cd /tools
# pip install -e .
python -m pip install --user -e .
cd /gdsc
tail -F /dev/null