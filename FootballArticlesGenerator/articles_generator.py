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


def generate_articles(file_name: str, short_output: bool, text_count: int):
    """
    Core function for generating articles.
    :param file_name: Name of the file.
    :param detailed_output: Bool value whether detailed output should be printed.
    :param text_count: Number of texts we would like to generate.
    """

    # transforming json file into inner representation of data as Data.Match class
    try:
        match_data: Data.Match = di.DataInitializer.init_match_data(file_name)
    except di.FileFormatEx as fe:
        print(fe.message)
        exit(0)

    # transforming data into document plan (list of messages)
    doc_plan: dp.DocumentPlan = dp.DocumentPlanner.plan_document(match_data)

    # printing overview of the match
    if not short_output:
        p.Printer.print_overview(doc_plan)

    random.seed(10)  # setting the seed for the whole program

    # creating many versions of the same article
    for i in range(text_count):
        # lexicalizing Messages into language-specific expressions
        # transforming those expressions into well-build input fo Genja API
        plain_article: (str, List[str]) = sp.SentencePlanner.lexicalize_article(doc_plan, match_data)

        # printing detailed output of article if needed
        if not short_output:
            p.Printer.print_detailed_output(match_data, doc_plan, plain_article)
            short_output = True  # detailed output only to be printed once

        # calling Geneea API on article
        try:
            article: (str, str) = lr.LinguisticRealiser.realise_article(plain_article)

            # printing article
            p.Printer.print_article(i, text_count, article)

        except lr.GenjaApiKeyEx as e:   # catching possible exception, when the Genja API key is incorrect
            print(e.message)
            exit(0)

