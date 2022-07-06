"""Generating the article and handles each module.
Input is the name of the json file (string) and output is the article (stdout).
"""

# Python's libraries
from typing import List
import random

# Other parts of the code
import Data
import data_initializer as di
import document_planner as dp
import printer as p
import sentence_planner as sp
import linguistic_realiser as lr


def generate_articles(file_name: str, detailed_output: bool, text_count: int):
    """
    Core function for generating articles.
    :param file_name: Name of the file.
    :param detailed_output: Bool value whether detailed output should be printed.
    :param text_count: Number of texts we would like to generate.
    """

    # transforming json file into inner representation of data as Data.Match class
    match_data: Data.Match = di.DataInitializer.init_match_data(file_name)

    # transforming data into document plan (list of messages)
    doc_plan: dp.DocumentPlan = dp.DocumentPlanner.plan_document(match_data)

    # printing overview of the match
    p.Printer.print_overview(doc_plan)

    random.seed(10)  # setting the seed for the whole program

    # creating many versions of the same article
    for i in range(text_count):
        # lexicalizing Messages into language-specific expressions
        # transforming those expressions into well-build input fo Geneea API
        plain_article: (str, List[str]) = sp.SentencePlanner.lexicalize_article(doc_plan, match_data)

        # calling Geneea API on article
        article: (str, str) = lr.LinguisticRealiser.realise_article(plain_article)

        # printing detailed output of article if needed
        if detailed_output:
            p.Printer.print_detailed_output(match_data, doc_plan, plain_article)
            detailed_output = False    # detailed output only to be printed once

        # printing article
        p.Printer.print_article(i, text_count, article)
