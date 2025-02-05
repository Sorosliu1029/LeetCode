"""
Convert .ipynb to .html by nbconvert
"""

import json
import os
from nbconvert import HTMLExporter
import re
import sys
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
import threading
from helper import get_folder_for, TEMPLATE_DIR, INDEX_HTML_PATH, PROBLEMS_JSON


def extract_problem_id(filename):
    return int(re.search(r"^(\d+)\.", filename).group(1))


class Converter(object):
    def __init__(self):
        self.html_exporter = HTMLExporter()
        self.html_exporter.exclude_input_prompt = True
        self.html_exporter.exclude_output_prompt = True

    def convert(self, ipynb_path):
        return self.html_exporter.from_filename(ipynb_path)

    def write(self, problem_id, source_ipynb_path):
        assert os.path.exists(source_ipynb_path)
        body, resources = self.convert(source_ipynb_path)
        name = resources["metadata"]["name"]

        directory = os.path.join("docs", get_folder_for(problem_id, 100))
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        write_filename = os.path.join(directory, "{}.html".format(name))
        with open(write_filename, "wt", encoding="utf-8") as f:
            f.write(body)
        return "{} write success".format(write_filename)


def convert(problem_id):
    solved_problems = dict()
    suffix_filter = lambda f: f.endswith(".ipynb") and not f.endswith("__no-ac.ipynb")

    if problem_id:
        direcotry = get_folder_for(problem_id, 50)
        for _, _, filenames in os.walk(direcotry):
            for filename in filter(
                lambda f: f.startswith("{}.".format(problem_id)) and suffix_filter(f),
                filenames,
            ):
                solved_problems[problem_id] = os.path.join(direcotry, filename)
    else:
        for dirpath, _, filenames in os.walk("."):
            if re.search(r"(\d+)-(\d+)$", dirpath):
                for filename in filter(suffix_filter, filenames):
                    source_ipynb_path = os.path.join(dirpath, filename)
                    problem_id = extract_problem_id(filename)
                    solved_problems[problem_id] = source_ipynb_path

    local = threading.local()

    def thread_initializer():
        local.converter = Converter()

    def converter_write(pid, path):
        return local.converter.write(pid, path)

    with ThreadPoolExecutor(max_workers=10, initializer=thread_initializer) as executor:
        for r in executor.map(
            converter_write, solved_problems.keys(), solved_problems.values()
        ):
            print(r)

    return solved_problems


def render_index(all_problems, solved_problems):
    solved_problem_ids = solved_problems.keys()
    solved_count = len(solved_problem_ids)
    total_valid_count = sum(1 for _ in filter(lambda p: p, all_problems))

    data = {
        "solved_count": solved_count,
        "total_count": len(all_problems),
        "total_valid_count": total_valid_count,
        "progress_percentage": "{}".format(solved_count * 100 // total_valid_count),
        "solved": set(solved_problem_ids),
        "problems": all_problems,
    }

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    readme_template = env.get_template("index.html.j2")
    readme_template.stream(**data).dump(INDEX_HTML_PATH)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0].isdigit():
        convert(int(args[0]))
        print("Convert question {} to html done".format(args[0]))
    else:
        solved_problems = convert(0)
        print("Convert to html done.")

        with open(PROBLEMS_JSON, "rt", encoding="utf-8") as f:
            all_problems = json.load(f)
        render_index(all_problems, solved_problems)
        print("Render index.html done.")
