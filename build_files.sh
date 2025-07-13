#!/bin/bash

# Install dependencies
pip3.9 install -r requirements.txt

# Run migrations
python3.9 manage.py migrate

# Collect static files
python3.9 manage.py collectstatic --noinput --clear

# Create staticfiles_build directory
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/
