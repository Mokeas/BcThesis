"""Generating the article and handles each module.
Input is the name of the json file (string) and output is the article (stdout).
"""

# Python's libraries
from typing import List
from dataclasses import dataclass
import random

# Other parts of the code
import Data
import data_initializer as di
import document_planner as dp
import overview_printer as op
import lexicalizer as lex
import realiser as real


def generate_article(filename: str, print_output: bool, text_count: int):
    """Core function for generating article."""

    # transforming json file into inner representation of data as Data.Match class
    match_data: Data.Match = di.DataInitializer.init_match_data(filename)
    # print(f'{match_data} \n\n ' + '_' * 70)

    # transforming data into document plan (list of messages)
    doc_plan: DP.DocumentPlan = dp.DocumentPlanner.plan_document(match_data)
    # print(f'{doc_plan} \n\n ' + '_' * 70)

    # printing overview of the match
    op.OverviewPrinter.print(doc_plan)

    random.seed(10)  # setting the seed for the whole program

    # creating many versions of the same article

    # creating list of articles - each of them is tuple of title(str) and sentences List(str)
    # articles are a well-build input for Geneea

    text_count = 1
    for i in range(text_count):

        plain_article: (str, List[str]) = lex.Lexicalizer.lexicalize_article(doc_plan, match_data)
        print(f'{plain_article} \n\n ' + '_' * 70)

        # calling Geneea API on every article, creating list of articles
        article: (str, List[str]) = real.Realizer.realize_article(plain_article)

        # printing article
        print(f'{article} \n\n ' + '_' * 70)

    """
        if print_output:
        print(f'{match_data} \n\n ' + '_' * 70)
        print(f'{doc_plan} \n\n ' + '_' * 70)
        print(f'{plain_str} \n\n ' + '_' * 70)
        print(f'{text} \n\n ' + '_' * 70)
    """
