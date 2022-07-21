"""Runs the generator - main.py"""

# Python's libraries
import argparse
from os.path import exists
# Other parts of the code
import articles_generator as ag


def run(args):
    """Main function to run the whole article generator with correct arguments."""
    ag.generate_articles(file_name=args.match_data, short_output=args.short_output, text_count=args.text_count)


def positive_integer(n):
    """Controls the requirement for positive integer."""
    try:
        number = int(n)
        if number <= 0:
            raise argparse.ArgumentTypeError("Number of texts to generate must be a positive integer.")
        return number

    except ValueError:
        raise argparse.ArgumentTypeError("Number of texts to generate must be a positive integer.")


def existing_file(file):
    """Controls the requirement for existing file."""
    if exists(file):
        return file
    else:
        raise argparse.ArgumentTypeError("File does not exist. Please select existing file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--match_data", default="example_match.json", type=existing_file, help="JSON file with match data.")
    parser.add_argument("-c", "--text_count", default=3, type=positive_integer, help="Number of generated texts.")
    parser.add_argument("-o", "--short_output", action='store_true', help="Prints detailed output. If false, prints only result articles.")

    args_ = parser.parse_args([] if "__file__" not in globals() else None)
    run(args_)
