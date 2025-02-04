#!/usr/bin/env python3
import sys
from generator import generate_notebook

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Please provide question id")
        raise SystemExit(1)
    
    question_id = int(args[0])
    generate_notebook(question_id)