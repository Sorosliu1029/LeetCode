import os
import json
import requests
import time
import datetime
from IPython.display import Markdown, display

LEETCODE = 'https://leetcode.com'

def printmd(string):
    display(Markdown(string))

def get_question_solution(notebook_cells):
    for cell in notebook_cells:
        if cell['cell_type'] == 'code' and ('class Solution:' in ''.join(cell['source']) or cell['metadata'].get('isSolutionCode')):
            solution = ''.join(cell['source']) 
            return solution if not solution.endswith('pass') else None

def login_leetcode(s):
    login_url = '{domain}/accounts/login/'.format(domain=LEETCODE)
    boundary = '------WebKitFormBoundaryLeetCode'
    # FIXME: LeetCode add Google recaptcha to enforce login, so auto login not working any more 😭️
    body_template = '{boundary}\r\nContent-Disposition: form-data; name="login"\r\n\r\n{login}\r\n{boundary}\r\nContent-Disposition: form-data; name="password"\r\n\r\n{password}\r\n{boundary}\r\nContent-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n{csrftoken}\r\n{boundary}--\r\n'
    
    if not os.path.exists(os.path.join('..', 'account.json')):
        raise RuntimeError('Must create "account.json" file first.')
    
    with open(os.path.join('..', 'account.json'), 'rt') as f:
        myaccount = json.load(f)

    login = myaccount['login']
    password = myaccount['password']
    csrftoken = s.cookies.get('csrftoken', domain='leetcode.com', path='/')
    assert login
    assert password
    assert csrftoken

    headers = {
        'Referer': login_url,
        'x-csrftoken': csrftoken,
        'Content-Type': 'multipart/form-data; boundary={boundary}'.format(boundary=boundary[2:]),
        'Cache-Control': "no-cache"
    }
    body = body_template.format(boundary=boundary, login=login, password=password, csrftoken=csrftoken)

    resp = s.post(login_url, data=body, headers=headers)
    cookies = dict(s.cookies)
    success_msg = 'Successfully signed in as'
    if resp.ok and 'LEETCODE_SESSION' in cookies and success_msg in cookies['messages']:
        return True
    resp.raise_for_status()

"""
instead of use `login_leetcode`, attach leetcode session directly
"""
def attach_leetcode_session(s):
    if not os.path.exists(os.path.join('..', 'account.json')):
        raise RuntimeError('Must create "account.json" file first.')

    with open(os.path.join('..', 'account.json'), 'rt') as f:
        myaccount = json.load(f)
    
    leetcode_session = myaccount['leetcode_session']
    assert leetcode_session

    s.cookies.set('LEETCODE_SESSION', leetcode_session)
    return True

def submit_solution(s, submit_url, solution, question_id, sample_testcase):
    full_submit_url = 'https://leetcode.com{submit_url}'.format(submit_url=submit_url)
    csrftoken = s.cookies.get('csrftoken', domain='leetcode.com', path='/')
    assert csrftoken

    headers = {
        'Referer': LEETCODE,
        'x-csrftoken': csrftoken,
        'Content-Type': 'application/json'
    }
    submission = {
        'question_id': str(question_id),
        'data_input': sample_testcase,
        'lang': 'python3',
        'typed_code': solution,
        'test_mode': False,
        'judge_type': 'large'
    }

    resp = s.post(full_submit_url, json=submission, headers=headers)
    if resp.ok:
        return resp.json()
    resp.raise_for_status()

def check_submission_result(s, submission_id):
    check_url = '{domain}/submissions/detail/{submission_id}/check/'.format(domain=LEETCODE, submission_id=submission_id)
    resp = s.get(check_url)
    if resp.ok:
        return resp.json()
    resp.raise_for_status()

def submit(question_id):
    files = list(filter(os.path.isfile, os.listdir()))
    for f in files:
        if f.startswith('{id}.'.format(id=question_id)) and f.endswith('.ipynb'):
            notebook_file = f
            break
    else:
        return { 'ERROR': 'Notebook not found for id: {id}'.format(id=question_id) }

    with open(notebook_file, 'rt') as f:
        notebook = json.load(f)
    
    solution = get_question_solution(notebook['cells'])
    submit_url = notebook['metadata']['leetcode_question_info']['submitUrl']
    sample_testcase = notebook['metadata']['leetcode_question_info']['sampleTestCase']

    if not solution:
        return { 'ERROR': 'No solution or solution is empty' }
    if not submit_url:
        return { 'ERROR': 'No submit url' }
    if not sample_testcase:
        return { 'ERROR': 'No sample test case' }

    with requests.Session() as s:
        s.get('{domain}'.format(domain=LEETCODE))
        # if login_leetcode(s):
        if attach_leetcode_session(s):
            submission = submit_solution(s, submit_url, solution, question_id, sample_testcase)
            assert submission
            submission_id = submission['submission_id']
            time.sleep(1)
            submission_result = check_submission_result(s, submission_id)
            check_cnt = 0
            while submission_result['state'] == 'PENDING' or submission_result['state'] == 'STARTED':
                time.sleep(2)
                check_cnt += 1
                if check_cnt > 30:
                    return { 'ERROR': 'Check submission for too long time. Submission ID: {submission_id}'.format(submission_id=submission_id) }
                submission_result = check_submission_result(s, submission_id)

#             print(submission_result)

            printmd('😃 Result: {status_msg}\n\n📥 Input: `{input}`\n\n📤 Output: `{output}`\n\n✅ Expected: `{excepted}`\n\n💯 Passed Test Case: {passed} / {total}\n\n🚀 Runtime: {runtime}, Memory: {memory}\n\n🉑 Runtime Percentile: better than {runtime_percentile:.2f}%, Memory Percentile: better than {memory_percentile:.2f}%\n\n📆 Finished At: {finished_at}'
                    .format(
                        status_msg=submission_result.get('status_msg', ''),
                        input=submission_result.get('input_formatted', ''),
                        output=submission_result.get('code_output', ''),
                        excepted=submission_result.get('expected_output', ''),
                        passed=submission_result.get('total_correct', ''),
                        total=submission_result.get('total_testcases', ''),
                        runtime=submission_result.get('status_runtime', ''),
                        runtime_percentile=submission_result.get('runtime_percentile', ''),
                        memory=submission_result.get('status_memory', ''),
                        memory_percentile=submission_result.get('memory_percentile', ''),
                        finished_at=datetime.datetime.fromtimestamp(submission_result.get('task_finish_time', 0) / 1000).strftime("%Y-%m-%d")
                    )
            )
        else:
            printmd(' ⚠️ Login LeetCode failed')