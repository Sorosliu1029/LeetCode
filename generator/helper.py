import os

LEETCODE = "https://leetcode.com"
TEMPLATE_PATH = os.path.join("docs", "templates")
INDEX_HTML_PATH = os.path.join("docs", "index.html")
PROBLEMS_JSON = "questions.json"
NOTEBOOK_TEMPLATE_JSON = 'notebook.template.json'

def get_folder_for(question_id, interval):
    interval_start = (question_id-1) // interval * interval + 1
    return "{}-{}".format(interval_start, interval_start+interval-1)