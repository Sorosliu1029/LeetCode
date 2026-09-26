#!/usr/bin/env zsh

# run in current shell
# `source ./launch-jupyter.sh`

echo "Activating conda environment 'leetcode'..."
conda activate leetcode

echo "Setting PYTHONPATH..."
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Launching Jupyter Lab..."
jupyter lab --LabApp.extension_manager="readonly"

echo "Done"
