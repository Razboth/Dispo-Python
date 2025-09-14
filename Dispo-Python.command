#!/bin/bash

# macOS desktop launcher for Dispo-Python
# Double-click this file to run the application

# Get the directory where this script is located
cd "$(dirname "$0")"

# Run the main launcher in interactive mode
./run.sh

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press Enter to close..."
    read
fi