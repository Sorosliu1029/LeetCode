#!/usr/bin/python3
"""
Use LeetCode's GraphQL API to generate question notebook
"""
import requests
import json
import sys
import os

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

    query="""{
        "operationName": "getQuestionDetail",
        "query": 
            "query 
                getQuestionDetail($titleSlug: String!) 
                    {
                        question(titleSlug: $titleSlug) 
                            { 
                                questionId
                                content
                            }
                    }",
        "variables": {
            "titleSlug": "%s"
        }
    }"""

    headers = {
        'x-csrftoken': csrf_token,
        'Refer': 'https://leetcode.com',
        'Content-Type': 'application/json',
        'Cache-Control': "no-cache"
    }

    print(headers)
    print(query % title_slug)
    print(s.cookies)
    resp = s.post(
            '{domain}{url}'.format(domain=LEETCODE, url='graphql'),
            json=(query % title_slug),
            headers=headers
       )
    
    if resp.ok:
        print('ok here')
        question_info = resp.json()
        print(question_info)
    
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


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Please provide question id")
        raise SystemExit(1)
    
    question_id = int(args[0])
    main(question_id)