#!/usr/bin/env python

import json
from generator import PROBLEMS_JSON, convert_notebook_to_html, render_index_html


if __name__ == "__main__":
    solved_problems = convert_notebook_to_html()
    print("Convert to html done.")

    with open(PROBLEMS_JSON, "rt", encoding="utf-8") as f:
        all_problems = json.load(f)
    render_index_html(all_problems, solved_problems)
    print("Render index.html done.")
