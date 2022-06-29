"""Runs the generator - main.py"""

# Python's libraries
import argparse
# Other parts of the code
import articles_generator as ag


def run(args):
    """Main function to run the whole article generator with correct arguments."""
    ag.generate_articles(file_name=args.match_data, detailed_output=True, text_count=args.text_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_data", default="0Ao9H20P.json", type=str, help="JSON file with match data.")
    parser.add_argument("--text_count", default=3, type=int, help="Number of generated texts.")
    parser.add_argument("--test", default=False, type=bool, help="Testing for errors in each match.")
    parser.add_argument("--output", default="", type=str, help="Path for output file.")
    args_ = parser.parse_args([] if "__file__" not in globals() else None)
    run(args_)
