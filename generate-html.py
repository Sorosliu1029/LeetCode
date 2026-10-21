"""
Convert .ipynb to .html by nbconvert
"""

import datetime
import email.utils
import html
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from jinja2 import Environment, FileSystemLoader
from nbconvert import HTMLExporter
from nbconvert.preprocessors import Preprocessor

TEMPLATE_DIR = "docs"
INDEX_HTML_PATH = os.path.join("docs", "index.html")
NOTEBOOK_TEMPLATE_DIR = "templates"
GITHUB_BLOB_URL = "https://github.com/Sorosliu1029/LeetCode/blob/master/"


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


def split_sections(source):
    """Split markdown into {heading: body} by its '#### ' headings."""
    sections = {}
    heading = None
    for line in source.splitlines():
        if line.startswith("#### "):
            heading = line[5:].strip()
            sections[heading] = []
        elif heading is not None:
            sections[heading].append(line)
    return {h: "\n".join(body).strip() for h, body in sections.items()}


def render_meta(source):
    sections = split_sections(source)
    parts = []
    for heading in sections:
        m = re.match(r"Difficulty:\s*(\w+),\s*AC rate:\s*([\d.]+%)", heading)
        if m:
            parts.append(
                '<span class="pill {}">{}</span><span class="ac">AC rate {}</span>'.format(
                    m.group(1).lower(), m.group(1), m.group(2)
                )
            )
    if "Topics:" in sections:
        tags = [t.strip() for t in sections["Topics:"].split("|")]
    else:
        tags = [t.lstrip("- ").strip() for t in sections.get("Question Tags:", "").splitlines()]
    parts.append(
        '<ul class="tags">{}</ul>'.format(
            "".join("<li>{}</li>".format(html.escape(t)) for t in tags if t)
        )
    )
    links = re.findall(r"\[(?:Question )?([^\]]+)\]\(([^)]+)\)", sections.get("Links:", ""))
    parts.append(
        '<span class="links">{}</span>'.format(
            "".join('<a href="{}" target="_blank" rel="noopener">{}</a>'.format(url, text) for text, url in links)
        )
    )
    meta = '<div class="meta">{}</div>'.format("".join(parts))
    hints = sections.get("Hints:")
    if hints:
        meta += "\n\n<details class=\"hints\"><summary>Hints</summary>\n\n{}\n\n</details>".format(hints)
    return meta


def render_result(source):
    fields = {}
    for line in source.splitlines():
        line = re.sub(r"^\S+\s+", "", line.strip())  # drop the leading emoji
        for pair in re.split(r",\s*(?=[A-Z][\w ]*:)", line):
            label, _, value = pair.partition(":")
            value = value.strip().strip("`").strip()
            if value:
                fields[label.strip()] = value

    def finished_date():
        value = fields.get("Finished At", "")
        try:
            return email.utils.parsedate_to_datetime(value).date().isoformat()
        except (TypeError, ValueError):
            return value  # older notebooks already store a bare date

    def beats(label):
        value = fields.get(label, "")
        return '<small>beats {}</small>'.format(html.escape(value[len("better than "):])) if value else ""

    stats = [
        ("Result", html.escape(fields.get("Result", ""))),
        ("Tests", html.escape(fields.get("Passed Test Case", ""))),
        ("Runtime", html.escape(fields.get("Runtime", "")) + beats("Runtime Percentile")),
        ("Memory", html.escape(fields.get("Memory", "")) + beats("Memory Percentile")),
    ]
    stats.append(("Finished", html.escape(finished_date())))
    # failing cases can be huge, so they get full-width rows below the stats
    cases = [(label, "<code>{}</code>".format(html.escape(fields[label]))) for label in ("Input", "Output", "Expected") if label in fields]
    status = "accepted" if fields.get("Result") == "Accepted" else "rejected"
    return '<dl class="result {}">{}{}</dl>'.format(
        status,
        "".join("<div><dt>{}</dt><dd>{}</dd></div>".format(k, v) for k, v in stats if v),
        "".join('<div class="case"><dt>{}</dt><dd>{}</dd></div>'.format(k, v) for k, v in cases),
    )


def is_result(source):
    return "Result:" in source and "Passed Test Case" in source


class NotebookStyler(Preprocessor):
    """Tag the standard cells of a solution notebook and tidy their markdown."""

    def preprocess(self, nb, resources):
        page = resources.setdefault("page", {})
        cells = []
        meta_cell = None
        statement_tagged = False
        for cell in nb.cells:
            source = cell.source
            tag = None
            if cell.cell_type == "markdown":
                m = re.match(r"^###\s+(\d+)\.\s+(.*)$", source.strip())
                if m:
                    tag = "title"
                    page["title"] = m.group(2)
                    cell.source = '<p class="pid">#{}</p>\n\n# {}'.format(m.group(1), m.group(2))
                elif "#### Difficulty" in source:
                    tag = "meta"
                    cell.source = render_meta(source)
                elif re.match(r"^#### (Test Case|Sample Test Case)", source):
                    tag = "tests"
                    cell.source = source.split("\n", 1)[1] if "\n" in source else ""
                elif "What's your idea?" in source:
                    tag = "idea"
                    lines = [l for l in source.strip().splitlines() if l.strip() not in ("---", "What's your idea?")]
                    cell.source = "\n".join(lines).strip()
                elif is_result(source):
                    tag = "result"
                    cell.source = render_result(source)
                elif not statement_tagged:
                    tag = "statement"
                    statement_tagged = True
                    source = re.sub(r"^#### Content\s*\n", "", source)
                    cell.source = re.sub(r"<p>(&nbsp;|\s)*</p>", "", source)
                if "$" in cell.source:
                    page["has_math"] = True
            elif cell.cell_type == "code":
                for output in cell.get("outputs", []):
                    md = output.get("data", {}).get("text/markdown")
                    if md and is_result(md):
                        tag = "submit"
                        output["data"]["text/markdown"] = render_result(md)
            if tag:
                cell.metadata["tags"] = list(cell.metadata.get("tags", [])) + [tag]
            if tag == "meta":
                meta_cell = cell
            else:
                cells.append(cell)
        if meta_cell is not None:
            titles = [i for i, c in enumerate(cells) if "title" in c.metadata.get("tags", [])]
            cells.insert(titles[0] + 1 if titles else 0, meta_cell)
        nb.cells = cells
        return nb, resources


class Converter(object):
    def __init__(self):
        self.html_exporter = HTMLExporter(
            template_name="notebook", extra_template_basedirs=[NOTEBOOK_TEMPLATE_DIR]
        )
        self.html_exporter.exclude_input_prompt = True
        self.html_exporter.exclude_output_prompt = True
        self.html_exporter.register_preprocessor(NotebookStyler(), enabled=True)

    def convert(self, ipynb_path, page):
        return self.html_exporter.from_filename(ipynb_path, resources={"page": page})

    def write(self, problem_id, source_ipynb_path, neighbours=(None, None)):
        assert os.path.exists(source_ipynb_path)
        page = {
            "id": problem_id,
            "source": GITHUB_BLOB_URL + os.path.relpath(source_ipynb_path),
            "prev": neighbours[0],
            "next": neighbours[1],
        }
        body, resources = self.convert(source_ipynb_path, page)
        name = resources["metadata"]["name"]

        directory = os.path.join("docs", get_folder_for(problem_id, 100))
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        write_filename = os.path.join(directory, "{}.html".format(name))
        with open(write_filename, "wt", encoding="utf-8") as f:
            f.write(body)
        return "{} write success".format(write_filename)


def page_link(problem_id, ipynb_path):
    name = os.path.splitext(os.path.basename(ipynb_path))[0]
    return {
        "id": problem_id,
        "href": "../{}/{}.html".format(get_folder_for(problem_id, 100), name),
    }


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

    # previous / next solved problem, for the pager on each notebook page
    ids = sorted(solved_problems)
    links = [page_link(pid, solved_problems[pid]) for pid in ids]
    neighbours = {
        pid: (links[i - 1] if i > 0 else None, links[i + 1] if i + 1 < len(ids) else None)
        for i, pid in enumerate(ids)
    }

    def converter_write(pid, path):
        return local.converter.write(pid, path, neighbours[pid])

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
