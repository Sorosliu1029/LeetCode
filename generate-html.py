#!/usr/bin/env python
"""
Convert .ipynb to .html by nbconvert
"""
import os
from nbconvert import HTMLExporter
import re

TEMPLATE_PATH = os.path.join('docs', 'templates')
INDEX_HTML_PATH = os.path.join('docs', 'index.html')

INTERVAL = 50

def extract_problem_id(filename):
    return int(re.search(r'^(\d+)\.', filename).group(1))


class Converter(object):
    def __init__(self):
        self.html_exporter = HTMLExporter()
        self.html_exporter.template_path = [os.path.join('docs', 'templates')]
        self.html_exporter.template_file = 'full'

    def convert(self, ipynb_path):
        return self.html_exporter.from_filename(ipynb_path)

    def write(self, source_ipynb_path):
        assert os.path.exists(source_ipynb_path)
        body, resources = self.convert(source_ipynb_path)
        name = resources['metadata']['name']
        problem_id = extract_problem_id(name)

        interval_start = (problem_id-1) // INTERVAL * INTERVAL + 1
        directory = os.path.join(
            'docs', '{}-{}'.format(interval_start, interval_start + INTERVAL-1))
        if not os.path.exists(directory):
            os.mkdir(directory)
        write_filename = os.path.join(directory, '{}.html'.format(name))
        with open(write_filename, 'wt', encoding='utf-8') as f:
            f.write(body)
        print('{} write success'.format(write_filename))


def convert():
    solved_problems = dict()

    for dirpath, _, filenames in os.walk('.'):
        if re.search(r'(\d+)-(\d+)$', dirpath):
            for filename in filter(lambda f: f.endswith('.ipynb'), filenames):
                source_ipynb_path = os.path.join(dirpath, filename)
                problem_id = extract_problem_id(filename)
                solved_problems[problem_id] = {
                    'source_ipynb_path': source_ipynb_path
                }

    converter = Converter()
    for problem_id in solved_problems:
        converter.write(solved_problems[problem_id]['source_ipynb_path'])

    return solved_problems


def render_index(solved_problems):
    # TODO: index.html
    pass


def main():
    solved_problems = convert()
    print('Convert to html done.')
    render_index(solved_problems)
    print('Render index.html done.')


if __name__ == '__main__':
    main()
