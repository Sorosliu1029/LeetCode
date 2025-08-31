#!/usr/bin/env zsh

echo "Activating conda environment 'leetcode'..."
conda activate leetcode

echo "Setting PYTHONPATH..."
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Launching Jupyter Lab..."
jupyter lab

echo "Done"
