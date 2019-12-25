#!/bin/bash
ls -A1 $1/*.py | xargs pylint -v