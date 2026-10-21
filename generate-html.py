"""
Convert .ipynb to .html by nbconvert
"""

import datetime
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from jinja2 import Environment, FileSystemLoader
from nbconvert import HTMLExporter

TEMPLATE_DIR = "docs"
INDEX_HTML_PATH = os.path.join("docs", "index.html")


def get_folder_for(question_id, interval):
    interval_start = (question_id - 1) // interval * interval + 1
    return "{}-{}".format(interval_start, interval_start + interval - 1)


def extract_problem_id(filename):
    m = re.search(r"^(\d+)\.", filename)
    assert m is not None, "Cannot extract problem id from filename: {}".format(filename)
    return int(m.group(1))


def get_all_problems():
    response = requests.post(
        url="https://leetcode.com/graphql",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "query": "query allQuestions { allQuestions { questionFrontendId titleSlug title difficulty isPaidOnly topicTags { name } } }"
            }
        ),
    )
    response.raise_for_status()
    data = response.json()
    all_problems = [
        {
            "id": int(q["questionFrontendId"]),
            "slug": q["titleSlug"],
            "title": q["title"],
            "difficulty": q["difficulty"],
            "paid": q["isPaidOnly"],
            "tags": [t["name"] for t in q["topicTags"] or []],
        }
        for q in data["data"]["allQuestions"]
        if q["questionFrontendId"].isdigit()
    ]
    filtered_all_problems = [p for p in all_problems if p["id"] < 10000]
    max_id = max(p["id"] for p in filtered_all_problems)
    problems = [None] * (max_id + 1)
    for p in filtered_all_problems:
        problems[p["id"]] = p
    return problems


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
        directory = get_folder_for(problem_id, 50)
        for _, _, filenames in os.walk(directory):
            for filename in filter(
                lambda f: f.startswith("{}.".format(problem_id)) and suffix_filter(f),
                filenames,
            ):
                solved_problems[problem_id] = os.path.join(directory, filename)
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
    tags = sorted({t for p in all_problems if p for t in p["tags"]})
    tag_index = {t: i for i, t in enumerate(tags)}
    difficulties = ["Easy", "Medium", "Hard"]
    stats = {d: {"solved": 0, "total": 0} for d in difficulties}

    cells = []
    for pid in range(1, len(all_problems)):
        p = all_problems[pid]
        if not p:
            cells.append(None)
            continue
        solved = pid in solved_problems
        stats[p["difficulty"]]["total"] += 1
        if solved:
            stats[p["difficulty"]]["solved"] += 1
            filename = os.path.splitext(os.path.basename(solved_problems[pid]))[0]
            href = "{}/{}.html".format(get_folder_for(pid, 100), filename)
        else:
            href = "https://leetcode.com/problems/{}/".format(p["slug"])
        cells.append(
            dict(
                p,
                solved=solved,
                href=href,
                tag_ids=" ".join(str(tag_index[t]) for t in p["tags"]),
            )
        )

    solved_count = len(solved_problems)
    total_valid_count = sum(s["total"] for s in stats.values())

    data = {
        "solved_count": solved_count,
        "total_valid_count": total_valid_count,
        "progress_percentage": "{:.1f}".format(solved_count * 100 / total_valid_count),
        "blocks": [cells[i : i + 100] for i in range(0, len(cells), 100)],
        "stats": stats,
        "tags": tags,
        "updated": datetime.date.today().isoformat(),
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

        try:
            all_problems = get_all_problems()
        except Exception as e:
            print("Failed to get all problems from LeetCode:", e)
            sys.exit(1)

        render_index(all_problems, solved_problems)
        print(
            f"Render index.html done. Solved {len(solved_problems)} problems out of {len(all_problems)-1}."
        )
