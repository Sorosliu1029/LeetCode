#!/usr/bin/env zsh

# run in current shell
# `source ./launch-jupyter.sh`

echo "Activating uv virtual environment '.venv'..."
source .venv/bin/activate

echo "Setting PYTHONPATH..."
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Launching Jupyter Lab..."
jupyter lab --LabApp.extension_manager="readonly"

echo "Done"
