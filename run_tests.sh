#!/bin/bash
source env/bin/activate
pip install .
rm -rf testdir
python -m pytest tests
