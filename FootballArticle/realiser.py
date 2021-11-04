# Brief description:

# performs linguistic transformation on lexicalized text using Geneea
# input: (str, List[str])
# output: str

# -----------------------------------------------------
# Python's libraries
import json
import os
import requests
from typing import List

# Other parts of the code


class Realizer:
    @staticmethod
    def realize_str(plain_str: (str, List[str])) -> str:
        return f'{plain_str[0]}\n' + "\n" + ("\n".join(plain_str[1]))

    @staticmethod
    def create_json_file_for_geneea(plain_str: (str, List[str]), file_path: str):
        data = {'templates': []}
        to_print = plain_str[0] + ' ' + ' '.join(plain_str[1])
        data['templates'].append({
            "id": "tmpl-2",
            "name": "body template",
            "body": to_print
        })

        data['data'] = {}
        with open(file_path, 'w') as output_json:
            json.dump(data, output_json)

    @staticmethod
    def realize_article(plain_str: (str, List[str])) -> str:
        file_path = r'C:\Users\danra\Skola\MFF\RP\SP_FootballArticle\geneea_input.json'
        Realizer.create_json_file_for_geneea(plain_str, file_path)

        with open(file_path) as json_file:
            output_geneea: dict = Realizer.call_geneea(json.load(json_file))

        return output_geneea['article']

    @staticmethod
    def call_geneea(json_file: dict):
        url = 'https://generator.geneea.com/generate'
        headers = {
            'content-type': 'application/json',
            'Authorization': os.getenv('GENJA_API_KEY')
        }
        return requests.post(url, json=json_file, headers=headers).json()
