import argparse
import article_generator as ag


def run(args):
    ag.generate_article(args.match_data, print_output=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match_data", default="0Ao9H20P.json", type=str, help="JSON file with match data.")
    parser.add_argument("--test", default=False, type=bool, help="Testing for errors in each match.")
    parser.add_argument("--output", default="", type=str, help="Path for output file.")
    args_ = parser.parse_args([] if "__file__" not in globals() else None)
    run(args_)