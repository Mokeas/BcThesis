"""Module to print overview of the match (same way Livesport.cz does it)."""

# Other parts of the code
import document_planner as dp
import Types


class OverviewPrinter:
    """Class handling printing of the overview of the match."""
    line_width = 113
    side_border_char = '|'
    top_border_char = '_'
    top_header_char = '_'
    bottom_border_char = '_'
    middle_border_char = '|'
    message_bullet = '#'
    time_delimiter = '->'

    @staticmethod
    def print(doc_plan: dp.DocumentPlan):
        """Core method for printing overview. Takes one argument, which is a doc_plan."""
        print(' OVERVIEW:')
        OverviewPrinter.print_top_border()
        OverviewPrinter.print_header(doc_plan.title)
        OverviewPrinter.print_half_time_header(1)

        half_time_printed = False
        for msg in doc_plan.body:
            if msg.time.base > 45 and not half_time_printed:
                OverviewPrinter.print_half_time_header(2)
                half_time_printed = True
            OverviewPrinter.print_message(msg)
            OverviewPrinter.print_empty_line()

        OverviewPrinter.print_bottom_border()

    @staticmethod
    def print_half_time_header(ht: int):
        print(OverviewPrinter.side_border_char + (OverviewPrinter.line_width - 2) * OverviewPrinter.top_header_char + OverviewPrinter.side_border_char)
        text = '2nd HALF'
        if ht == 1:
            text = '1st HALF'
        space_count = OverviewPrinter.line_width - 2 - 2 - len(text)
        print(OverviewPrinter.side_border_char + '  ' + text + space_count * ' ' + OverviewPrinter.side_border_char)
        print(OverviewPrinter.side_border_char + (OverviewPrinter.line_width - 2) * OverviewPrinter.top_header_char + OverviewPrinter.side_border_char)

    @staticmethod
    def print_empty_line():
        space_count = int((OverviewPrinter.line_width - 3) / 2)
        print(OverviewPrinter.side_border_char + space_count * ' ' + OverviewPrinter.middle_border_char + space_count * ' ' + OverviewPrinter.side_border_char)

    @staticmethod
    def print_top_border():
        print(OverviewPrinter.top_border_char * OverviewPrinter.line_width)

    @staticmethod
    def print_bottom_border():
        print(OverviewPrinter.bottom_border_char * OverviewPrinter.line_width)

    @staticmethod
    def print_message(msg: dp.Messages):
        semi_line_empty = int(((OverviewPrinter.line_width - 3) / 2)) * ' '

        first_line_data = ' ' + OverviewPrinter.message_bullet + ' ' + str(msg.time) + \
                          ' ' + OverviewPrinter.time_delimiter + ' ' + OverviewPrinter.get_message_title(msg)
        first_line_space_count: int = int(((OverviewPrinter.line_width - 3) / 2) - len(first_line_data))
        first_line_data += first_line_space_count * ' '

        second_line_data = ' ' + OverviewPrinter.get_message_participant(msg)
        second_line_space_count: int = int(((OverviewPrinter.line_width - 3) / 2) - len(second_line_data))
        second_line_data += second_line_space_count * ' '

        if msg.team.type == Types.Team.HOME:
            print(OverviewPrinter.side_border_char + first_line_data + OverviewPrinter.middle_border_char +
                  semi_line_empty + OverviewPrinter.side_border_char)
            print(OverviewPrinter.side_border_char + second_line_data + OverviewPrinter.middle_border_char +
                  semi_line_empty + OverviewPrinter.side_border_char)
        else:
            print(OverviewPrinter.side_border_char + semi_line_empty + OverviewPrinter.middle_border_char +
                  first_line_data + OverviewPrinter.side_border_char)
            print(OverviewPrinter.side_border_char + semi_line_empty + OverviewPrinter.middle_border_char +
                  second_line_data + OverviewPrinter.side_border_char)

    @staticmethod
    def print_header(msg: dp.Messages.Result):
        OverviewPrinter.print_empty_line()
        team_home = msg.team_home.name
        team_away = msg.team_away.name
        print(OverviewPrinter.get_team_str(home=True, team=team_home) + OverviewPrinter.get_team_str(home=False, team=team_away))
        OverviewPrinter.print_empty_line()
        score = msg.score
        print(OverviewPrinter.get_team_str(home=True, team=str(score.goals_home)) + OverviewPrinter.get_team_str(home=False, team=str(score.goals_away)))
        OverviewPrinter.print_empty_line()

    @staticmethod
    def get_team_str(home: bool, team: str) -> str:
        chars_per_team = (OverviewPrinter.line_width - 3) / 2
        home_space_count: int = int((chars_per_team - len(team)) // 2)
        leftover = 0
        if (chars_per_team - len(team)) % 2 == 1:
            leftover = 1

        middle_str =+ home_space_count * ' ' + team + home_space_count * ' ' + leftover * ' '
        if home:
            return OverviewPrinter.side_border_char + middle_str + OverviewPrinter.middle_border_char
        else:
            return middle_str + OverviewPrinter.side_border_char

    @staticmethod
    def get_message_title(msg: dp.Messages) -> str:
        if type(msg) == dp.Messages.Card:
            if msg.card_type == Types.Card.YELLOW:
                return 'YELLOW CARD'
            elif msg.card_type == Types.Card.RED_AUTO:
                return 'YELLOW CARD -> RED CARD'
            else:
                return 'RED CARD'
        elif type(msg) == dp.Messages.Goal:
            if msg.goal_type == Types.Goal.PENALTY:
                return 'GOAL - PENALTY'
            elif msg.goal_type == Types.Goal.ASSISTANCE or msg.goal_type == Types.Goal.SOLO_PLAY:
                return 'GOAL'
            else:
                return 'OWN GOAL'
        elif type(msg) == dp.Messages.Substitution:
            return 'SUBSTITUTION'
        elif type(msg) == dp.Messages.MissedPenalty:
            return 'MISSED PENALTY'
        else:
            pass

    @staticmethod
    def get_message_participant(msg: dp.Messages) -> str:
        if type(msg) == dp.Messages.Card or type(msg) == dp.Messages.MissedPenalty:
            return msg.participant.get_short_name()
        elif type(msg) == dp.Messages.Goal:
            if msg.goal_type == Types.Goal.ASSISTANCE:
                return msg.participant.get_short_name() + ' (' + msg.assistance.get_short_name() + ')'
            else:
                return msg.participant.get_short_name()
        elif type(msg) == dp.Messages.Substitution:
            return '(out) ' + msg.participant_out.get_short_name() + ' <-> (in) ' + msg.participant_in.get_short_name()
        else:
            pass
