"""Module that performs linguistic transformation on lexicalized text using Genja.
Input is tuple of title and list of sentences with needed transformation for Genja.
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
    Text needs to be in a form that Genja API requires - supplemented by linguistic commands."""

    @staticmethod
    def __create_json_file_for_genja(plain_str: str, file: str):
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
        with open(file, 'w') as output_json:
            json.dump(data, output_json)

    @staticmethod
    def __get_aux_file_name(title: bool) -> str:
        """
        Creates json file name for title or body.
        :param title: title (True), body (False)
        :return: File name
        """
        file_name_header = 'geneea_input_'
        file_file_format = '.json'
        if title:
            file_type = 'title'
        else:
            file_type = 'body'

        return file_name_header + file_type + file_file_format

    @staticmethod
    def __realise_str(title: bool, plain_str: str, key: str) -> str:
        """
        Realizes plain string (title or body) to string after performing lexical realisation.
        :param title: title (True), body (False)
        :param plain_str: string as well-build input for Geneea
        :return: text string
        """
        file = LinguisticRealiser.__get_aux_file_name(title=title)
        LinguisticRealiser.__create_json_file_for_genja(plain_str, file)
        with open(file) as json_file:
            output_genja: dict = LinguisticRealiser.__call_genja(json.load(json_file), key)
        os.remove(file)     # deleting file
        return output_genja['article']

    @staticmethod
    def realise_article(plain_str: (str, List[str]), key: str) -> (str, str):
        """
        Core function for realisation of the article.
        :param plain_str:
        :return: Tuple of strings - title and body of the article.
        """

        title: str = LinguisticRealiser.__realise_str(title=True, plain_str=plain_str[0], key=key)
        body: str = LinguisticRealiser.__realise_str(title=False, plain_str=' '.join(plain_str[1]), key=key)
        return title, body

    @staticmethod
    def __call_genja(json_file: dict, key: str):
        """
        Calls Genja API with correct parameters and performs lexical realisation.
        :param json_file: json file as an input for Genja request
        """
        url = 'https://generator.geneea.com/generate'
        headers = {
            'content-type': 'application/json',
            # authorization key is stored internally to enable code to be public
            'Authorization': key
        }
        response = requests.post(url, json=json_file, headers=headers)
        if response.status_code == 401:
            raise GenjaApiKeyEx()
        else:
            return response.json()


class GenjaApiKeyEx(Exception):
    def __init__(self, message="ERROR: Articles can not be generated. Key for Genja API is incorrect."):
        self.message = message
        super().__init__(self.message)
