"""
Convert .ipynb to .html by nbconvert
"""

import os
from nbconvert import HTMLExporter
from jinja2 import Environment, FileSystemLoader
import re
from .helper import TEMPLATE_PATH, INDEX_HTML_PATH, get_folder_for


def extract_problem_id(filename):
    return int(re.search(r"^(\d+)\.", filename).group(1))


class Converter(object):
    def __init__(self):
        self.html_exporter = HTMLExporter()
        self.html_exporter.template_path = [os.path.join("docs", "templates")]
        self.html_exporter.template_file = "full"
        self.html_exporter.exclude_input_prompt = True
        self.html_exporter.exclude_output_prompt = True

    def convert(self, ipynb_path):
        return self.html_exporter.from_filename(ipynb_path)

    def write(self, source_ipynb_path):
        assert os.path.exists(source_ipynb_path)
        body, resources = self.convert(source_ipynb_path)
        name = resources["metadata"]["name"]
        problem_id = extract_problem_id(name)

        directory = os.path.join("docs", get_folder_for(problem_id, 100))
        if not os.path.exists(directory):
            os.mkdir(directory)
        write_filename = os.path.join(directory, "{}.html".format(name))
        with open(write_filename, "wt", encoding="utf-8") as f:
            f.write(body)
        print("{} write success".format(write_filename))


def convert():
    solved_problems = dict()

    for dirpath, _, filenames in os.walk("."):
        if re.search(r"(\d+)-(\d+)$", dirpath):
            for filename in filter(
                lambda f: f.endswith(".ipynb") and not f.endswith("__no-ac.ipynb"),
                filenames,
            ):
                source_ipynb_path = os.path.join(dirpath, filename)
                problem_id = extract_problem_id(filename)
                solved_problems[problem_id] = {"source_ipynb_path": source_ipynb_path}

    converter = Converter()
    for problem_id in solved_problems:
        converter.write(solved_problems[problem_id]["source_ipynb_path"])

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

    env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
    readme_template = env.get_template("index.html.j2")
    readme_template.stream(**data).dump(INDEX_HTML_PATH)
