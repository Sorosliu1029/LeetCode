#!/usr/bin/python3
"""
Use LeetCode's GraphQL API to generate question notebook
"""
import requests
import json
import sys
import os
import re

LEETCODE = 'https://leetcode.com/'

def get_question_list(session):
    resp = session.get('{domain}{url}'.format(domain=LEETCODE, url='api/problems/algorithms/'))
    if resp.ok:
        questions = resp.json()['stat_status_pairs']
        max_id = max((q['stat']['frontend_question_id'] for q in questions))
        question_list = [None] * (max_id+1)
        get_desired_info = lambda q: (q['stat']['frontend_question_id'], q['stat']['question__title_slug'])
        for q in map(get_desired_info, questions):
            question_list[q[0]] = q[1]
        return question_list

def get_question_info(s, title_slug):
    csrf_token = s.cookies.get('csrftoken', domain='leetcode.com', path='/')
    assert csrf_token is not None

    query = """
        query getQuestionDetail($titleSlug: String!)
            {
                question(titleSlug: $titleSlug)
                {
                    questionFrontendId
                    questionTitleSlug
                    questionTitle
                    content
                    sampleTestCase
                    questionDetailUrl
                    difficulty
                    discussUrl
                    topicTags
                    codeDefinition
                    submitUrl                                      
                }
            }"""

    graphql_query = {
        "operationName": "getQuestionDetail",
        "query": query,
        "variables": {
            "titleSlug": title_slug
        }
    }

    headers = {
        'x-csrftoken': csrf_token,
        'Referer': 'https://leetcode.com',
        'Content-Type': 'application/json',
        'Cache-Control': "no-cache"
    }

    resp = s.post(
            '{domain}{url}'.format(domain=LEETCODE, url='graphql'),
            json=graphql_query,
            headers=headers,
       )
    
    if resp.ok:
        question_info = resp.json()
        return question_info

def get_code_definition(code_definitions, language='python3'):
    for code_definition in code_definitions:
        if code_definition['value'] == language:
            return code_definition['defaultCode']
    
def generate_notebook(question_id, question_info):
    with open('notebook.template.json', 'rt') as f:
        template = json.load(f)

    template['metadata']['language_info']['version'] = "{}.{}.{}".format(*sys.version_info[:3])
    template['metadata']['leetcode_question_info']['submitUrl'] = question_info['submitUrl']
    template['metadata']['leetcode_question_info']['sampleTestCase'] = question_info['sampleTestCase']

    template['cells'][0]['source'] = ['### {frontend_id}. {title}'.format(frontend_id=question_info['questionFrontendId'], title=question_info['questionTitle'])]
    template['cells'][1]['source'] = [ '#### Content\n', question_info['content'] ]
    template['cells'][2]['source'] = [ '#### Sample Test Case\n', question_info['sampleTestCase'] ]
    template['cells'][3]['source'] = [
            '#### Difficulty: {}\n\n'.format(question_info['difficulty']),
            '#### Question Tags:\n'
        ] + \
        list(map(lambda t: '- {}\n'.format(t['name']), json.loads(question_info['topicTags']))) + \
        [
            '\n',
            '[Question Detail](https://leetcode.com{}description/)\n\n'.format(question_info['questionDetailUrl']),
            '[Question Discussion]({})'.format(question_info['discussUrl'])
        ]
    code_definition = get_code_definition(json.loads(question_info['codeDefinition']))
    assert code_definition is not None
    template['cells'][5]['source'] = [
            code_definition + 'pass'
        ]
    func_match = re.search(r'class Solution:\s+def (.*?)\(self,', code_definition)
    func_name = func_match[1]
    template['cells'][6]['source'] = [
                "import sys, os; sys.path.append(os.path.abspath('..'))\n",
                'from timer import timethis\n',
                's = Solution()\n',
                '{func} = timethis(s.{func})\n'.format(func=func_name),
                '{func}()'.format(func=func_name)
        ]
    template['cells'][7]['source'] = [
        'from submitter import submit\n',
        'submit({id})'.format(id=question_id)
    ]
    
    interval_start = (question_id-1) // 25 * 25 + 1
    directory = "{}-{}".format(interval_start, interval_start+24)
    if not os.path.exists(directory):
        os.mkdir(directory)

    with open(os.path.join(directory, '{id}.{title}.ipynb'.format(id=question_id, title=question_info['questionTitleSlug'])), 'w+') as f:
        json.dump(template, f, indent=2)


def main(question_id):
    with requests.Session() as s:
        s.head('{domain}'.format(domain=LEETCODE))

        if os.path.exists('questions.json'):
            with open('questions.json', 'rt') as f:
                question_list = json.load(f)
        else:
            question_list = get_question_list(s)
            with open('questions.json', 'wt') as f:
                json.dump(question_list, f)
        
        question_title_slug = question_list[question_id]
        assert question_title_slug is not None

        question_info = get_question_info(s, question_title_slug)
    
    question_info = question_info['data']['question']
    assert int(question_info['questionFrontendId']) == question_id
    assert question_info['questionTitleSlug'] == question_title_slug

    generate_notebook(question_id, question_info)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Please provide question id")
        raise SystemExit(1)
    
    question_id = int(args[0])
    main(question_id)