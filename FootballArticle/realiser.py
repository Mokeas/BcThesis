"""Module that performs linguistic transformation on lexicalized text using Geneea.
Input is tuple of title and list of sentences with needed transformation for Geneea.
Output is a complete article as string."""

# -----------------------------------------------------
# Python's libraries
import json
import os
import requests
from typing import List


class Realizer:
    """Realizer class performing the final realization of the modified text.
    Text needs to be in a form that Geneea requires - supplemented by linguistic commands."""
    @staticmethod
    def format_str(plain_str: (str, List[str])) -> str:   # ToDo: rename
        """Prints plain string into article - title and then each sentence on it's own line."""
        return f'{plain_str[0]}\n' + "\n" + ("\n".join(plain_str[1]))

    @staticmethod
    def create_json_file_for_geneea(plain_str: (str, List[str]), file_path: str):
        """Creates json file that can be then entered as input of Geneea."""
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
        """Core function for realization of the article. Returns article as string."""
        file_path = r'C:\Users\danra\Skola\MFF\RP\SP_FootballArticle\geneea_input.json'
        formatted_plain_str = Realizer.format_str(plain_str)
        Realizer.create_json_file_for_geneea(formatted_plain_str, file_path)

        with open(file_path) as json_file:
            output_geneea: dict = Realizer.call_geneea(json.load(json_file))

        return output_geneea['article']

    @staticmethod
    def call_geneea(json_file: dict):
        """Calls Geneea rest API with correct params."""
        url = 'https://generator.geneea.com/generate'
        headers = {
            'content-type': 'application/json',
            # authorization key is stored internally to enable code to be public
            'Authorization': os.getenv('GENJA_API_KEY')
        }
        return requests.post(url, json=json_file, headers=headers).json()
