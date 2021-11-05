# Brief description:

# core method handler: generating article
# input: name of json file
# output: (stdout) article

# -----------------------------------------------------
# Python's libraries
from typing import List
from dataclasses import dataclass
import random

# Other parts of the code
import Data
import data_initializer as DI
import document_planner as DP
import lexicalizer as lex
import realiser as real
# -----------------------------------------------------


def generate_article(filename: str, print_output: bool, text_count: int):
    match_data: Data.Match = DI.DataInitializer.init_match_data(filename)
    #print(f'{match_data} \n\n ' + '_' * 70)

    doc_plan: DP.DocumentPlan = DP.DocumentPlanner.plan_document(match_data)
    #print(f'{doc_plan} \n\n ' + '_' * 70)

    random.seed(10)  # setting the seed for whole program
    for x in range(text_count):

        plain_str: (str, List[str]) = lex.Lexicalizer.lexicalize(doc_plan, match_data)
        # print(f'{plain_str} \n\n ' + '_' * 70)

        text: str = real.Realizer.realize_str(plain_str)

        if print_output:
            print(f'{match_data} \n\n ' + '_' * 70)
            print(f'{doc_plan} \n\n ' + '_' * 70)
            print(f'{plain_str} \n\n ' + '_' * 70)
            print(f'{text} \n\n ' + '_' * 70)

        # calling Geneea rest API
        article = real.Realizer.realize_article(plain_str)
        print(f'{article} \n\n ' + '_' * 70)
