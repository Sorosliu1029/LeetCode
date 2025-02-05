#!/usr/bin/env python3
"""
Use LeetCode's GraphQL API to generate question notebook
"""
import sys
import os
import requests
import json
import sys
import os
import re
import time
import random
from helper import (
    get_folder_for,
    patch_csrf_token,
    LEETCODE,
    NOTEBOOK_TEMPLATE_JSON,
    PROBLEMS_JSON,
)


def get_question_list(session):
    resp = session.get(
        "{domain}{url}".format(domain=LEETCODE, url="/api/problems/algorithms/")
    )
    if resp.ok:
        questions = resp.json()["stat_status_pairs"]
        max_id = max((q["stat"]["frontend_question_id"] for q in questions))
        question_list = [None] * (max_id + 1)
        get_desired_info = lambda q: (
            q["stat"]["frontend_question_id"],
            q["stat"]["question__title_slug"],
        )
        for q in map(get_desired_info, questions):
            question_list[q[0]] = q[1]
        return question_list


def get_question_info(s, title_slug):
    csrf_token = s.cookies.get("csrftoken", domain="leetcode.com", path="/")
    assert csrf_token is not None

    query = """
query questionData($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        submitUrl
        questionDetailUrl
        boundTopicId
        title
        titleSlug
        content
        isPaidOnly
        difficulty
        likes
        dislikes
        isLiked
        similarQuestions
        exampleTestcases
        topicTags {
            name
            slug
            translatedName
            __typename
        }
        codeSnippets {
            lang
            langSlug
            code
            __typename
        }
        stats
        hints
        solution {
            id
            canSeeDetail
            paidOnly
            hasVideoSolution
            paidOnlyVideo
            __typename
        }
        status
        sampleTestCase
        __typename
    }
}"""

    graphql_query = {
        "operationName": "questionData",
        "query": query,
        "variables": {"titleSlug": title_slug},
    }

    headers = {
        "x-csrftoken": csrf_token,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    resp = s.post(
        "{domain}{url}".format(domain=LEETCODE, url="/graphql"),
        json=graphql_query,
        headers=headers,
    )

    if resp.ok:
        question_info = resp.json()
        return question_info


def get_code_snippet(code_snippets, language="python3"):
    for code_snippet in code_snippets:
        if code_snippet["langSlug"] == language:
            return code_snippet["code"]


def generate(question_id, question_info):
    with open(NOTEBOOK_TEMPLATE_JSON, "rt") as f:
        template = json.load(f)

    template["metadata"]["language_info"]["version"] = "{}.{}.{}".format(
        *sys.version_info[:3]
    )
    template["metadata"]["leetcode_question_info"]["submitUrl"] = question_info[
        "submitUrl"
    ]
    template["metadata"]["leetcode_question_info"]["sampleTestCase"] = question_info[
        "sampleTestCase"
    ]
    template["metadata"]["leetcode_question_info"]["questionId"] = question_info[
        "questionId"
    ]
    template["metadata"]["leetcode_question_info"]["questionFrontendId"] = (
        question_info["questionFrontendId"]
    )

    template["cells"][0]["source"] = [
        "### {frontend_id}. {title}".format(
            frontend_id=question_info["questionFrontendId"],
            title=question_info["title"],
        )
    ]
    template["cells"][1]["source"] = ["#### Content\n", question_info["content"]]
    template["cells"][2]["source"] = (
        [
            "#### Difficulty: {}, AC rate: {}\n\n".format(
                question_info["difficulty"],
                json.loads(question_info["stats"])["acRate"],
            ),
            "#### Question Tags:\n",
        ]
        + list(map(lambda t: "- {}\n".format(t["name"]), question_info["topicTags"]))
        + [
            "\n#### Links:\n",
            " 🎁 [Question Detail](https://leetcode.com{}description/)".format(
                question_info["questionDetailUrl"]
            )
            + " | 🎉 [Question Solution](https://leetcode.com{}solution/)".format(
                question_info["questionDetailUrl"]
            )
            + " | 💬 [Question Discussion](https://leetcode.com{}discuss/?orderBy=most_votes)\n".format(
                question_info["questionDetailUrl"]
            ),
            "\n#### Hints:\n",
        ]
        + [
            "<details><summary>Hint {}  🔍</summary>{}</details>\n".format(idx, hint)
            for idx, hint in enumerate(question_info["hints"])
        ]
    )
    template["cells"][3]["source"] = [
        "#### Sample Test Case\n",
        question_info["sampleTestCase"],
    ]

    code_snippet = get_code_snippet(question_info["codeSnippets"])
    assert code_snippet is not None

    pre_solution_index = code_snippet.find("class Solution:")
    pre_solution = None
    if pre_solution_index > 0:
        pre_solution = code_snippet[:pre_solution_index]
        code_snippet = code_snippet[pre_solution_index:]

    template["cells"][5]["source"] = [code_snippet + "pass"]
    template["cells"][5]["metadata"]["isSolutionCode"] = True

    func_match = re.search(r"class Solution:\s+def (.*?)\(self,", code_snippet)
    if func_match:
        func_name = func_match[1]
        template["cells"][6]["source"] = [
            "s = Solution()\n",
            "s.{func}()".format(func=func_name),
        ]
    template["cells"][7]["source"] = [
        "import sys, os; sys.path.append(os.path.abspath('..'))\n",
        "from submitter import submit\n",
        "submit({id})".format(id=question_id),
    ]

    if pre_solution:
        template["cells"].insert(
            5,
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [pre_solution.strip(" \n")],
            },
        )

    directory = get_folder_for(question_id, 50)
    if not os.path.exists(directory):
        os.mkdir(directory)

    file_path = os.path.join(
        directory,
        "{id}.{title}.ipynb".format(id=question_id, title=question_info["titleSlug"]),
    )
    with open(file_path, "w+") as f:
        json.dump(template, f, indent=2)
    print("Generation done. Notebook at " + file_path)


def generate_notebook(question_id):
    with requests.Session() as s:
        patch_csrf_token(s)

        if (
            not os.path.exists(PROBLEMS_JSON)
            or ((time.time() - os.path.getmtime(PROBLEMS_JSON)) // (60 * 60 * 24 * 30))
            > 3
        ):
            print("refresh " + PROBLEMS_JSON)
            question_list = get_question_list(s)
            with open(PROBLEMS_JSON, "wt") as f:
                json.dump(question_list, f)
        else:
            with open(PROBLEMS_JSON, "rt") as f:
                question_list = json.load(f)

        question_title_slug = question_list[question_id]
        assert question_title_slug is not None

        question_info = get_question_info(s, question_title_slug)

    question_info = question_info["data"]["question"]

    assert int(question_info["questionFrontendId"]) == question_id
    assert question_info["titleSlug"] == question_title_slug

    generate(question_id, question_info)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Please provide question id")
        raise SystemExit(1)

    question_id = int(args[0])
    generate_notebook(question_id)
