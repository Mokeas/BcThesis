"""Module to handle printing various outputs in a certain form."""

# Python's libraries
from typing import List

# Other parts of the code
import document_planner as dp
import Types
import Data


class Printer:
    """Class handling printing of the overview of the match."""

    # constants for changing looks of the output
    LINE_WIDTH = 113
    BORDER_SIDE = '|'
    BORDER_TOP = '_'
    BORDER_BOTTOM = '_'
    BORDER_MIDDLE = '|'
    HEADER_TOP = '_'
    MESSAGE_BULLET = '#'
    DELIMITER_TIME = '->'
    ARTICLE_WIDTH = LINE_WIDTH
    DELIMITER_OUTPUT = ''

    @staticmethod
    def print_overview(doc_plan: dp.DocumentPlan):
        """
        Core method for printing overview of the match (same way Livesport.cz does it)
        :param doc_plan: DocumentPlan
        """

        print()
        print(' OVERVIEW:')
        Printer.__print_top_border()
        Printer.__print_header(doc_plan.title)
        Printer.__print_half_time_header(1)

        half_time_printed = False
        for msg in doc_plan.body:
            if msg.time.base > 45 and not half_time_printed:
                Printer.__print_half_time_header(2)
                half_time_printed = True
            Printer.__print_message(msg)
            Printer.__print_empty_line()

        Printer.__print_bottom_border()
        print()

    @staticmethod
    def __print_half_time_header(ht: int):
        """
        Auxiliary function for overview print - prints half time header.
        :param ht: Number of half
        """
        print(Printer.BORDER_SIDE + (Printer.LINE_WIDTH - 2) * Printer.HEADER_TOP + Printer.BORDER_SIDE)
        text = '2nd HALF'
        if ht == 1:
            text = '1st HALF'
        space_count = Printer.LINE_WIDTH - 2 - 2 - len(text)
        print(Printer.BORDER_SIDE + '  ' + text + space_count * ' ' + Printer.BORDER_SIDE)
        print(Printer.BORDER_SIDE + (Printer.LINE_WIDTH - 2) * Printer.HEADER_TOP + Printer.BORDER_SIDE)

    @staticmethod
    def __print_empty_line():
        """Auxiliary function for overview print - prints empty line (split in the middle)."""
        space_count = int((Printer.LINE_WIDTH - 3) / 2)
        print(Printer.BORDER_SIDE + space_count * ' ' + Printer.BORDER_MIDDLE + space_count * ' ' + Printer.BORDER_SIDE)

    @staticmethod
    def __print_top_border():
        """Auxiliary function for overview print - prints top border."""
        print(Printer.BORDER_TOP * Printer.LINE_WIDTH)

    @staticmethod
    def __print_bottom_border():
        """Auxiliary function for overview print - prints bottom border."""
        print(Printer.BORDER_BOTTOM * Printer.LINE_WIDTH)

    @staticmethod
    def __print_message(msg: dp.Message):
        """Auxiliary function for overview print - prints message (one incident)."""
        semi_line_empty = int(((Printer.LINE_WIDTH - 3) / 2)) * ' '

        first_line_data = ' ' + Printer.MESSAGE_BULLET + ' ' + str(msg.time) + \
                          ' ' + Printer.DELIMITER_TIME + ' ' + Printer.__get_message_title(msg)
        first_line_space_count: int = int(((Printer.LINE_WIDTH - 3) / 2) - len(first_line_data))
        first_line_data += first_line_space_count * ' '

        second_line_data = ' ' + Printer.__get_message_participant(msg)
        second_line_space_count: int = int(((Printer.LINE_WIDTH - 3) / 2) - len(second_line_data))
        second_line_data += second_line_space_count * ' '

        if msg.team.type == Types.Team.HOME:
            print(Printer.BORDER_SIDE + first_line_data + Printer.BORDER_MIDDLE +
                  semi_line_empty + Printer.BORDER_SIDE)
            print(Printer.BORDER_SIDE + second_line_data + Printer.BORDER_MIDDLE +
                  semi_line_empty + Printer.BORDER_SIDE)
        else:
            print(Printer.BORDER_SIDE + semi_line_empty + Printer.BORDER_MIDDLE +
                  first_line_data + Printer.BORDER_SIDE)
            print(Printer.BORDER_SIDE + semi_line_empty + Printer.BORDER_MIDDLE +
                  second_line_data + Printer.BORDER_SIDE)

    @staticmethod
    def __print_header(msg: dp.Message.Result):
        """
        Auxiliary function for overview print - prints header of the match.
        :param msg: Result message
        """

        Printer.__print_empty_line()
        team_home = msg.team_home.name
        team_away = msg.team_away.name
        print(Printer.__get_team_str(home=True, team=team_home) + Printer.__get_team_str(home=False, team=team_away))
        Printer.__print_empty_line()
        score = msg.score
        print(Printer.__get_team_str(home=True, team=str(score.goals_home)) +
              Printer.__get_team_str(home=False, team=str(score.goals_away)))
        Printer.__print_empty_line()

    @staticmethod
    def __get_team_str(home: bool, team: str) -> str:
        """
        Auxiliary function for overview print - returns team name with the correct indentation and border characters.
        :param home: If not home, then the Team is away.
        :param team: Name of the Team.
        :return: Printable string.
        """
        chars_per_team = (Printer.LINE_WIDTH - 3) / 2
        home_space_count: int = int((chars_per_team - len(team)) // 2)
        leftover = 0
        if (chars_per_team - len(team)) % 2 == 1:
            leftover = 1

        middle_str = home_space_count * ' ' + team + home_space_count * ' ' + leftover * ' '
        if home:
            return Printer.BORDER_SIDE + middle_str + Printer.BORDER_MIDDLE
        else:
            return middle_str + Printer.BORDER_SIDE

    @staticmethod
    def __get_message_title(msg: dp.Message) -> str:
        """
        Auxiliary function for overview print - creates title for Message.
        :param msg: Message
        :return: String of message title to be printed
        """
        if type(msg) == dp.Message.Card:
            if msg.card_type == Types.Card.YELLOW:
                return 'YELLOW CARD'
            elif msg.card_type == Types.Card.RED_AUTO:
                return 'YELLOW CARD -> RED CARD'
            else:
                return 'RED CARD'
        elif type(msg) == dp.Message.Goal:
            if msg.goal_type == Types.Goal.PENALTY:
                return 'GOAL - PENALTY'
            elif msg.goal_type == Types.Goal.ASSISTANCE or msg.goal_type == Types.Goal.SOLO_PLAY:
                return 'GOAL'
            else:
                return 'OWN GOAL'
        elif type(msg) == dp.Message.Substitution:
            return 'SUBSTITUTION'
        elif type(msg) == dp.Message.MissedPenalty:
            return 'MISSED PENALTY'
        else:
            pass

    @staticmethod
    def __get_message_participant(msg: dp.Message) -> str:
        """
        Auxiliary function for overview print - extracts participant's name from message.
        :param msg: Message
        :return: Name of the player
        """
        if type(msg) == dp.Message.Card or type(msg) == dp.Message.MissedPenalty:
            return msg.participant.get_short_name()
        elif type(msg) == dp.Message.Goal:
            if msg.goal_type == Types.Goal.ASSISTANCE:
                return msg.participant.get_short_name() + ' (' + msg.assistance.get_short_name() + ')'
            else:
                return msg.participant.get_short_name()
        elif type(msg) == dp.Message.Substitution:
            return '(out) ' + msg.participant_out.get_short_name() + ' <-> (in) ' + msg.participant_in.get_short_name()
        else:
            pass

    @staticmethod
    def print_article(n: int, max_n: int, article: (str, str)):
        """
        Prints article with couple of decent adjustments - number of article, justified and delimited.
        :param n: Number of article.
        :param max_n: Number of articles generated in total.
        :param article: Article as a tuple of string - title and body
        """
        print("Article No. " + str(n + 1) + "/" + str(max_n))
        print(article[0].center(Printer.ARTICLE_WIDTH))
        print()
        print(article[1].ljust(Printer.ARTICLE_WIDTH))
        Printer.__print_delimiter_line()

    @staticmethod
    def __print_delimiter_line():
        """Auxiliary function to print delimiter line to make output more readable."""
        print(Printer.DELIMITER_OUTPUT * Printer.ARTICLE_WIDTH)

    @staticmethod
    def print_detailed_output(match_data: Data.Match, doc_plan: dp.DocumentPlan, plain_article: (str, List[str])):
        """
        Prints detailed output - each part of the code is printed to get the basic understanding of the program.
        :param match_data: Data.Match
        :param doc_plan: DocumentPlan
        :param plain_article: Geneea input plain_article.
        """
        print(f'{match_data} \n\n' + '_' * Printer.ARTICLE_WIDTH)
        print(f'{doc_plan} \n\n' + '_' * Printer.ARTICLE_WIDTH)
        print(f'PLAIN TITLE:\n{plain_article[0]})')
        print(f'PLAIN ARTICLE:\n' + ("\n".join(plain_article[1])))
        print('_' * Printer.ARTICLE_WIDTH)

