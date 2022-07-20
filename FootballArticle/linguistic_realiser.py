"""Module that performs linguistic transformation on lexicalized text using Geneea.
Input is tuple of title and list of sentences with needed transformation for Geneea.
Output is a tuple of title (str) and complete article as string."""

# -----------------------------------------------------
# Python's libraries
import json
import os
import requests
from typing import List
import os


class LinguisticRealiser:
    """Realizer class performing the final realisation of the modified text.
    Text needs to be in a form that Geneea requires - supplemented by linguistic commands."""

    @staticmethod
    def __create_json_file_for_geneea(plain_str: str, file_path: str):
        """
        Creates json file that can be then entered as input of Geneea.
        :param plain_str: String which is well-build input for Geneea.
        :param file_path: Path to json file which will be now initialized.
        """

        data = {'templates': []}
        data['templates'].append({
            "id": "tmpl-2",
            "name": "body template",
            "body": plain_str
        })

        data['data'] = {}
        with open(file_path, 'w') as output_json:
            json.dump(data, output_json)

    @staticmethod
    def __get_aux_file(title: bool) -> str:
        """
        Creates json file name for title or body.
        :param title: title (True), body (False)
        :return: File name
        """
        file_name_header = 'geneea_input'
        file_file_format = '.json'
        if title:
            file_type = 'title'
        else:
            file_type = 'body'

        return os.path.abspath(os.getcwd()) + file_name_header + file_type + file_file_format

    @staticmethod
    def __realise_str(title: bool, plain_str: str) -> str:
        """
        Realizes plain string (title or body) to string after performing lexical realisation.
        :param title: title (True), body (False)
        :param plain_str: string as well-build input for Geneea
        :return: text string
        """
        file = LinguisticRealiser.__get_aux_file(title=title)
        LinguisticRealiser.__create_json_file_for_geneea(plain_str, file)
        with open(file) as json_file:
            output_geneea: dict = LinguisticRealiser.__call_geneea(json.load(json_file))
        return output_geneea['article']

    @staticmethod
    def realise_article(plain_str: (str, List[str])) -> (str, str):
        """
        Core function for realisation of the article.
        :param plain_str:
        :return: Tuple of strings - title and body of the article.
        """

        title: str = LinguisticRealiser.__realise_str(title=True, plain_str=plain_str[0])
        body: str = LinguisticRealiser.__realise_str(title=False, plain_str=' '.join(plain_str[1]))
        return title, body

    @staticmethod
    def __call_geneea(json_file: dict):
        """
        Calls Geneea API with correct parameters and performs lexical realisation.
        :param json_file: json file as an input for Geneea request
        """
        url = 'https://generator.geneea.com/generate'
        headers = {
            'content-type': 'application/json',
            # authorization key is stored internally to enable code to be public
            'Authorization': os.getenv('GENJA_API_KEY')
        }
        return requests.post(url, json=json_file, headers=headers).json()
