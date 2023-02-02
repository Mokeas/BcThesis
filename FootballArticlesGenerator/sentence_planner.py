"""Lexicalize document plan with specific language expressions and
also transforming lexicalized text into valid input for Geneea.
Input is document plan and match data, output is string that can be an input of Geneea API.
"""

# Python's libraries
import random
from typing import List, Tuple, Union
from dataclasses import dataclass
import copy
# Other parts of the code
import Types
import document_planner as dp
import Data


@dataclass(frozen=True)
class MorphParams:
    """Class to transform linguistic requirements into Geneea well-build input. """
    case: Types.Morph.Case
    tense: Types.Morph.Tense
    gender: Types.Morph.Gender
    ref: None
    agr: None

    @staticmethod
    def create(string_id: str):
        params: (Types.Morph.Case, Types.Morph.Tense, Types.Morph.Gender, str, str) \
            = MorphParams.__get_morph_params(string_id)
        return MorphParams(case=params[0], tense=params[1], gender=params[2], ref=params[3], agr=params[4])

    @staticmethod
    def __get_morph_params(string_id: str) -> (Types.Morph.Case, Types.Morph.Tense, Types.Morph.Gender, str, str):
        """
        Transforms string id into attributes of MorphParams.
        :param string_id: Id string.
        :return: Tuple of (case, tense, ref, agr)
        """

        if string_id == '':
            return None, None, None, None, None
        else:
            [case_id, tense_id, gender_id, ref_id, agr_id] = string_id.split('-')

            # . stands for non-defined parameter
            case = None if case_id == "." else Types.Morph.Case(int(case_id))
            tense = None if tense_id == "." else Types.Morph.Tense(int(tense_id))
            gender = None if gender_id == "." else Types.Morph.Gender(int(gender_id))
            ref = None if ref_id == "." else ref_id
            agr = None if agr_id == "." else agr_id

            return case, tense, gender, ref, agr

    def apply_to_string(self, constituent: str) -> str:
        """
        Applies morphological attributes and create simple string into well-build string for Geneea API interface.
        :param constituent: String
        :return: Geneea string
        """

        header = '{{' + f'\'{constituent}\'|morph('

        mp: List[str] = []  # morphological parameters
        all_none = True

        if self.case is not None:
            mp.append(f'Case={self.case.name.lower().capitalize()}')
            all_none = False

        if self.tense is not None:
            mp.append(f'Tense={self.tense.name.lower().capitalize()}')
            all_none = False

        if self.gender is not None:
            if self.gender == Types.Morph.Gender.MascA:
                mp.append("Gender=Masc")
                mp.append("Animacy=Anim")
            elif self.gender == Types.Morph.Gender.MascI:
                mp.append("Gender=Masc")
                mp.append("Animacy=Inan")
            else:   # fem/neut
                mp.append(f'Gender={self.gender.name.lower().capitalize()}')

            all_none = False

        morph_params = "\'" + "|".join(mp) + "\'"
        mp.clear()
        mp.append(morph_params)

        if self.ref is not None:
            mp.append(f'ref={self.ref}')
            all_none = False

        if self.agr is not None:
            mp.append(f'agr={self.agr}')
            all_none = False

        body = ", ".join(mp)

        return constituent if all_none else header + body + ')}}'


@dataclass
class TemplateFrequency:
    """Class to store frequency of every template according to it's string id."""
    id: str
    count: int
    unused_indices: List[int]   # indices of templates that haven't been used yet
    last_used: int

    @staticmethod
    def create(id_: str, count: int):
        """
        Creates instance of TemplateFrequency.
        :param id_: id of the template
        :param count: number of templates with the same id
        :return: TemplateFrequency
        """
        unused_indices = [i for i in range(count)]
        return TemplateFrequency(id=id_, count=count, unused_indices=unused_indices, last_used=-1)

    def remove_from_unused_indices(self, chosen_index: int):
        """
        Removes index from unused indices after using this particular template.
        :param chosen_index: index, that has just been used.
        """

        if self.unused_indices != 0:
            index = 0
            while index < len(self.unused_indices):
                if self.unused_indices[index] == chosen_index:
                    self.unused_indices.remove(chosen_index)
                    return   # break the while cycle, if chosen_index found
                index += 1


@dataclass(frozen=True)
class Template:
    """Class to store constituent templates. Has to arguments:
    1) id (str) - is to its type and subtype e.g. type = verb, subtype = lose
    2) string (str) - stores current string realization of the template
    (it takes data, transforms it into string and stores it).
    """
    id: str
    string: str

    @staticmethod
    def create(type_: str, subtype: str, string: str):
        """
        Creates immutable instance of Template.
        That is the reason we have to associate templates string with data immediately.
        :param type_: type of the template
        :param subtype: subtype of the template
        :param string: lexical expression for the template
        :return: Template
        """
        id_ = Template.__create_template_id(type_, subtype)
        return Template(id_, string)

    @staticmethod
    def __create_template_id(type_: str, subtype: str) -> str:
        """
        Transforms type and subtype into string id of the template.
        :param type_: Type of template
        :param subtype: Subtype of template.
        :return: Id of the template
        """

        return type_ + '-' + subtype

    def __str__(self):
        return '[id: ' + self.id + ' | string: ' + self.string + "]"


class TemplateHandler:
    """Class for handling template choices systematically.
    Stores information about used templates in frequency table,
    which is a list of the auxiliary TemplateFrequency class.
    """
    frequency_table: List[TemplateFrequency]
    previous_msg_time: Data.Time

    def __init__(self):
        """Initializing frequency table attribute."""
        # creating every template possible
        all_templates = TemplateHandler.__init_all_templates()
        # initializing frequency table from all possible templates
        self.frequency_table = TemplateHandler.__init_frequency_table(all_templates)
        self.previous_msg_time = None

    def get_previous_msg_time(self):
        return self.previous_msg_time

    @staticmethod
    def __init_all_templates() -> List[Template]:
        """Initializes every template that could be used."""
        templates_entities = TemplateHandler.__get_templates_entity(first_init=True, subtype='', data=None)
        templates_words = TemplateHandler.__get_templates_word(first_init=True, subtype='')
        templates_verbs = TemplateHandler.__get_templates_verb(first_init=True, subtype='')
        return templates_entities + templates_verbs + templates_words

    @staticmethod
    def __init_frequency_table(all_templates: List[Template]) -> List[TemplateFrequency]:
        """
        Initializes frequency table using all templates possible.
        :param all_templates: List of all possible templates.
        :return: initialized frequency table in form of List[TemplateFrequency]
        """

        index = 0
        ft: List[TemplateFrequency] = []

        # no sorting is needed since Template initializing is systematical
        while index + 1 < len(all_templates):
            (end_index, count) = TemplateHandler.__skip_to_next_template_type(all_templates, index)
            ft.append(TemplateFrequency.create(all_templates[index].id, count))
            index += 1

        return ft

    @staticmethod
    def __skip_to_next_template_type(all_templates: List[Template], start_index: int) -> (int, int):
        """
        Looping through templates of the same id.
        Takes list of all templates and starting index of the template to count frequency for.
        :param all_templates: List of all templates.
        :param start_index:  Start index of the list of all_templates.
        :return: tuple of ints - index where the same id template ends, count of the template.
        """
        index = start_index
        count = 1
        while index + 1 < len(all_templates) and all_templates[index].id == all_templates[index+1].id:
            index += 1
            count += 1

        return index, count

    @staticmethod
    def __get_templates_entity(first_init: bool, subtype: str, data) -> List[Template]:
        """
        Creates templates that can lexicalize entities.
        :param first_init: bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        :param subtype: subtype (e.g. 'goal').
        :param data: correct data entity (e.g. for initializing it is Data.Player, for time Data.Time, etc.).
        :return: List of entity templates.
        """

        def __init_time_templates():
            """Auxiliary function to create time templates."""
            def get_words_for_minutes(minute: int, dativ: bool) -> str:
                """
                Function transforms number of minutes suitably into a well-built expression.
                :param minute: number of minute that need to be expressed
                :param dativ: if the expression needs fourth(False) or third(True) case
                :return: string expression that describes number of minutes
                """
                if minute >= 10 and minute % 10 != 0:
                    return get_numerals_as_text(minute, dativ)
                elif minute < 10:
                    return transform_small_numbers(minute, dativ)
                elif minute % 10 == 0:
                    return transform_round_numbers(minute, dativ)
                else:  # should not occur
                    pass

            def get_numerals_as_text(minute: int, dativ: bool) -> str:
                """
                Function connects the word minute with the number in a correct form.
                :param minute: number of minute that need to be expressed
                :param dativ: if the expression needs fourth(False) or third(True) case
                :return: string expression that describes number of minutes
                """
                if dativ:
                    return str(minute) + ". " + "minutě"
                else:
                    return str(minute) + " " + "minut"

            def transform_small_numbers(minute: int, dativ: bool) -> str:
                """
                Transforms samll numbers (1-9) to an expression consisting only words (no numbers).
                :param minute: number of minute that need to be expressed
                :param dativ: if the expression needs fourth(False) or third(True) case
                :return: string expression that describes number of minutes
                """
                ret_val = ""
                if minute == 1:
                    ret_val = "první minutě" if dativ else "jednu minutu"
                elif minute == 2:
                    ret_val = "druhé minutě" if dativ else "dvě minuty"
                elif minute == 3:
                    ret_val = "třetí minutě" if dativ else "tři minuty"
                elif minute == 4:
                    ret_val = "čtvrté minutě" if dativ else "čtyři minuty"
                elif minute == 5:
                    ret_val = "paté minutě" if dativ else "pět minut"
                elif minute == 6:
                    ret_val = "šesté minutě" if dativ else "šest minut"
                elif minute == 7:
                    ret_val = "sedmé minutě" if dativ else "sedm minut"
                elif minute == 8:
                    ret_val = "osmé minutě" if dativ else "osm minut"
                elif minute == 9:
                    ret_val = "deváté minutě" if dativ else "devět minut"
                else:   # should not occur
                    pass

                return ret_val

            def transform_round_numbers(minute: int, dativ: bool) -> str:
                """
                Transforms round number with a chance of 50% to an expression consisting only words (no numbers).
                :param minute: number of minute that need to be expressed
                :param dativ: if the expression needs fourth(False) or third(True) case
                :return: string expression that describes number of minutes
                """

                ret_val = ""
                if minute == 10:
                    ret_val = "desáté minutě" if dativ else "deset minut"
                elif minute == 20:
                    ret_val = "dvacáté minutě" if dativ else "dvacet minut"
                elif minute == 30:
                    ret_val = "třicáté minutě" if dativ else "třicet minut"
                elif minute == 40:
                    ret_val = "čtyřicáté minutě" if dativ else "čtyřicet minut"
                elif minute == 50:
                    ret_val = "padesáté minutě" if dativ else "padesát minut"
                elif minute == 60:
                    ret_val = "šedesáté minutě" if dativ else "šedesát minut"
                elif minute == 70:
                    ret_val = "sedmdesáté minutě" if dativ else "sedmdesát minut"
                elif minute == 80:
                    ret_val = "osmdesáté minutě" if dativ else "osmdesát minut"
                elif minute == 90:
                    ret_val = "devadesáté minutě" if dativ else "devadesát minut"
                else:   # should not occur
                    pass

                if random.randint(0, 1) == 1:
                    return ret_val
                else:
                    return get_numerals_as_text(minute, dativ)

            entity_type = 'time'
            time: Data.Time = data

            if first_init:
                time = Data.Time.create(0, 0)    # creating random time for first_init

            if time.added != 0:  #
                if time.base == 45:  # first half
                    templates.append(Template.create(type_, entity_type,
                                                     f"v {get_words_for_minutes(time.added, True) if data is not None else ''} "
                                                     f"nastavení prvního poločasu"))
                    templates.append(Template.create(type_, entity_type,
                                                     f"{get_words_for_minutes(time.added, False) if data is not None else ''} "
                                                     f"po začátku nastaveného času prvního poločasu"))
                else:  # second half
                    templates.append(Template.create(type_, entity_type,
                                                     f"v {get_words_for_minutes(time.added, True) if data is not None else ''} "
                                                     f"nastavení druhého poločasu"))
                    templates.append(Template.create(type_, entity_type,
                                                     f"{get_words_for_minutes(time.added, False) if data is not None else ''} "
                                                     f"po začátku nastaveného času druhého poločasu"))
            else:
                templates.append(Template.create(type_, entity_type,
                                                 f"v {get_words_for_minutes(time.base, True) if data is not None else ''}"))

                templates.append(Template.create(type_, entity_type,
                                                 f"{get_words_for_minutes(time.base, False) if data is not None else ''} po začátku"))

                if time.base > 45:
                    templates.append(Template.create(type_, entity_type,
                                                 f"{get_words_for_minutes(time.base-45, False) if data is not None else ''} "
                                                 f"po začátku druhého poločasu"))

        def __init_player_templates():
            """Auxiliary function to create player templates."""
            entity_type = 'player'
            player: Data.Player = data

            templates.append(Template.create(type_, entity_type,
                                             player.full_name if data is not None else ''))
            templates.append(Template.create(type_, entity_type,
                                             player.get_full_name_reversed() if data is not None else ''))
            templates.append(Template.create(type_, entity_type,
                                             player.get_last_name() if data is not None else ''))
            templates.append(Template.create(type_, entity_type,
                                             f"hráč s číslem {player.number if data is not None else ''}"))

        def __init_team_templates():
            """Auxiliary function to create team templates."""
            entity_type = 'team'
            team: Data.Team = data

            templates.append(Template.create(type_, entity_type,
                                             team.name if data is not None else ''))

        def __init_score_templates():
            """Auxiliary function to create score templates."""
            entity_type = 'score'
            score: Data.Score = data

            templates.append(Template.create(type_, entity_type,
                                             f"{score.goals_home if data is not None else ''}:"
                                             f"{score.goals_away if data is not None else ''}"))

        type_ = 'e'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            __init_time_templates()
            __init_player_templates()
            __init_team_templates()
            __init_score_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'time':
            __init_time_templates()
        elif subtype == 'player':
            __init_player_templates()
        elif subtype == 'team':
            __init_team_templates()
        elif subtype == 'score':
            __init_score_templates()
        else:
            print("Type Unknown")

        return templates

    @staticmethod
    def __get_templates_word(first_init: bool, subtype: str) -> List[Template]:
        """
        Creates templates that can lexicalize certain words.
        :param first_init: bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        :param subtype: subtype of the word as string.
        :return: List of word templates.
        """

        def __init_goal_templates():
            """Auxiliary function to create goal templates."""
            word_type = 'goal'
            templates.append(Template.create(type_, word_type, 'gól'))
            templates.append(Template.create(type_, word_type, 'branka'))

        def __init_assistance_templates():
            """Auxiliary function to create assistance templates."""
            word_type = 'assistance'
            templates.append(Template.create(type_, word_type, 'asistence'))
            templates.append(Template.create(type_, word_type, 'nahrávka'))
            templates.append(Template.create(type_, word_type, 'přihrávka'))
            templates.append(Template.create(type_, word_type, 'pas'))

        def __init_penalty_templates():
            """Auxiliary function to create penalty templates."""
            word_type = 'penalty'
            templates.append(Template.create(type_, word_type, 'penalta'))
            templates.append(Template.create(type_, word_type, 'pokutový kop'))
            templates.append(Template.create(type_, word_type, 'jedenáctka'))

        def __init_own_goal_templates():
            """Auxiliary function to create own goal templates."""
            word_type = 'own_goal'
            templates.append(Template.create(type_, word_type, 'vlastňák'))
            templates.append(Template.create(type_, word_type, 'vlastní gól'))
            templates.append(Template.create(type_, word_type, 'vlastenec'))

        def __init_yellow_card_templates():
            """Auxiliary function to create yellow card templates."""
            word_type = 'yellow_card'
            templates.append(Template.create(type_, word_type, 'žlutý'))
            templates.append(Template.create(type_, word_type, 'žlutá karta'))

        def __init_red_card_templates():
            """Auxiliary function to create red card templates."""
            word_type = 'red_card'
            templates.append(Template.create(type_, word_type, 'červený'))
            templates.append(Template.create(type_, word_type, 'červená karta'))

        def __init_result_draw_templates():
            """Auxiliary function to create result(draw) templates."""
            word_type = 'draw'
            templates.append(Template.create(type_, word_type, 'remíza'))
            templates.append(Template.create(type_, word_type, 'plichta'))
            templates.append(Template.create(type_, word_type, 'nerozhodný výsledek'))

        def __init_result_lose_templates():
            """Auxiliary function to create result(lose) templates."""
            word_type = 'lose'
            templates.append(Template.create(type_, word_type, 'porážka'))
            templates.append(Template.create(type_, word_type, 'prohra'))
            templates.append(Template.create(type_, word_type, 'debakl'))
            templates.append(Template.create(type_, word_type, 'ostuda'))

        def __init_result_win_templates():
            """Auxiliary function to create result(win) templates."""
            word_type = 'win'
            templates.append(Template.create(type_, word_type, 'vítězství'))
            templates.append(Template.create(type_, word_type, 'výhra'))
            templates.append(Template.create(type_, word_type, 'zdar'))

        def __init_nice_templates():
            """Auxiliary function to create nice (adjective) templates."""
            word_type = 'nice'
            templates.append(Template.create(type_, word_type, 'krásný'))
            templates.append(Template.create(type_, word_type, 'pohledný'))
            templates.append(Template.create(type_, word_type, 'nádherný'))
            templates.append(Template.create(type_, word_type, 'pěkný'))

        def __init_action_templates():
            """Auxiliary function to create action templates."""
            word_type = 'action'
            templates.append(Template.create(type_, word_type, 'akce'))
            templates.append(Template.create(type_, word_type, 'kombinace'))
            templates.append(Template.create(type_, word_type, 'souhra'))

        type_ = 'w'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            __init_goal_templates()
            __init_assistance_templates()
            __init_penalty_templates()
            __init_own_goal_templates()
            __init_yellow_card_templates()
            __init_red_card_templates()
            __init_result_draw_templates()
            __init_result_lose_templates()
            __init_result_win_templates()
            __init_nice_templates()
            __init_action_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'goal':
            __init_goal_templates()
        elif subtype == 'assistance':
            __init_assistance_templates()
        elif subtype == 'penalty':
            __init_penalty_templates()
        elif subtype == 'own_goal':
            __init_own_goal_templates()
        elif subtype == 'yellow_card':
            __init_yellow_card_templates()
        elif subtype == 'red_card':
            __init_red_card_templates()
        elif subtype == 'draw':
            __init_result_draw_templates()
        elif subtype == 'lose':
            __init_result_lose_templates()
        elif subtype == 'win':
            __init_result_win_templates()
        elif subtype == 'nice':
            __init_nice_templates()
        elif subtype == 'action':
            __init_action_templates()
        else:
            pass

        return templates

    @staticmethod
    def __get_templates_verb(first_init: bool, subtype: str) -> List[Template]:
        """
        Creates templates that can lexicalize certain verbs.
        :param first_init: bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        :param subtype: subtype of the verb as string.
        :return: List of verb templates.
        """

        def __init_result_win_templates():
            """Auxiliary function to create win templates."""
            verb_type = 'win'
            templates.append(Template.create(type_, verb_type, 'porazit'))
            templates.append(Template.create(type_, verb_type, 'rozdrtit'))
            templates.append(Template.create(type_, verb_type, 'deklasovat'))

        def __init_result_draw_templates():
            """Auxiliary function to create draw templates."""
            verb_type = 'draw'
            templates.append(Template.create(type_, verb_type, 'remizovat'))

        def __init_result_lose_templates():
            """Auxiliary function to create lose templates."""
            verb_type = 'lose'
            templates.append(Template.create(type_, verb_type, 'prohrát'))

        def __init_goal_templates():
            """Auxiliary function to create goal templates."""
            verb_type = 'goal'
            templates.append(Template.create(type_, verb_type, 'vstřelit'))
            templates.append(Template.create(type_, verb_type, 'vsítit'))
            templates.append(Template.create(type_, verb_type, 'dát'))

        def __init_score_change_templates():
            """Auxiliary function to create change of score templates."""
            verb_type = 'score_change'
            templates.append(Template.create(type_, verb_type, 'změnit'))
            templates.append(Template.create(type_, verb_type, 'upravit'))
            templates.append(Template.create(type_, verb_type, 'zvýšit'))

        def __init_penalty_templates():
            """Auxiliary function to create penalty templates."""
            verb_type = 'penalty'
            templates.append(Template.create(type_, verb_type, 'proměnit'))
            templates.append(Template.create(type_, verb_type, 'dát'))

        def __init_failed_penalty_templates():
            """Auxiliary function to create failed penalty templates."""
            verb_type = 'failed_penalty'
            templates.append(Template.create(type_, verb_type, 'zpackat'))
            templates.append(Template.create(type_, verb_type, 'neproměnit'))
            templates.append(Template.create(type_, verb_type, 'nedat'))

        def __init_substitution_templates():
            """Auxiliary function to create substitution templates."""
            verb_type = 'substitution'
            templates.append(Template.create(type_, verb_type, 'střídat'))
            templates.append(Template.create(type_, verb_type, 'vystřídat'))

        def __init_card_templates():
            """Auxiliary function to create card templates."""
            verb_type = 'card'
            templates.append(Template.create(type_, verb_type, 'dostat'))
            templates.append(Template.create(type_, verb_type, 'obdržet'))
            templates.append(Template.create(type_, verb_type, 'vyfasovat'))

        type_ = 'v'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            __init_result_win_templates()
            __init_result_draw_templates()
            __init_result_lose_templates()
            __init_goal_templates()
            __init_score_change_templates()
            __init_penalty_templates()
            __init_failed_penalty_templates()
            __init_substitution_templates()
            __init_card_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'win':
            __init_result_win_templates()
        elif subtype == 'draw':
            __init_result_draw_templates()
        elif subtype == 'lose':
            __init_result_lose_templates()
        elif subtype == 'goal':
            __init_goal_templates()
        elif subtype == 'score_change':
            __init_score_change_templates()
        elif subtype == 'penalty':
            __init_penalty_templates()
        elif subtype == 'failed_penalty':
            __init_failed_penalty_templates()
        elif subtype == 'substitution':
            __init_substitution_templates()
        elif subtype == 'card':
            __init_card_templates()
        else:
            pass

        return templates

    @staticmethod
    def __get_possible_templates(id_: str, explicit_data: Types.ExplicitEntityData, msg: dp.Message) -> List[Template]:
        """
        Returns list of all possible templates given information about the cosnstituent.
        :param id_: String id of the templates.
        :param explicit_data: Type of explicit entity date (needed only for entity).
        :param msg: Message
        :return: List of all possible templates.
        """

        constituent_type: str = id_.split('-')[0]
        subtype: str = id_.split('-')[1]
        possibilities: List[Template] = []

        if constituent_type == 'e':  # ENTITY
            # data variable only used when const_type is entity
            data = TemplateHandler.__get_msg_data(explicit_data, msg)
            possibilities = TemplateHandler.__get_templates_entity(first_init=False, subtype=subtype, data=data)
        elif constituent_type == 'w':  # WORD
            possibilities = TemplateHandler.__get_templates_word(first_init=False, subtype=subtype)
        elif constituent_type == 'v':  # VERB
            possibilities = TemplateHandler.__get_templates_verb(first_init=False, subtype=subtype)
        else:
            pass

        return possibilities

    def get_template(self, id_: str, explicit_data: Types.ExplicitEntityData, msg: dp.Message) -> Template:
        """
        Core function for picking template for given constituent information.
        :param id_: String id of the templates.
        :param explicit_data: Type of explicit entity date (needed only for entity).
        :param msg: Message
        :return: picked Template
        """

        possibilities = TemplateHandler.__get_possible_templates(id_, explicit_data, msg)
        chosen_template = self.__choose_template(possibilities)
        if not type(msg) == dp.Message.Result:
            self.previous_msg_time = msg.time
        return chosen_template

    def __choose_template(self, possibilities: List[Template]) -> Template:
        """
        Chooses template from all possible templates using this algorithm:
        1) if we haven't used every template - pick one randomly
        2) if we already used every template once - pick randomly from every template possible
        (except the last used so that ensure some differentiation.)
        :param possibilities: List of possible templates.
        :return: Template
        """

        id_ = possibilities[0].id
        freq: TemplateFrequency = self.__get_template_frequency(id_)

        # we can add step 0) of algorithm - always choose the first template when first occurrence of template type
        '''
        if freq.count == len(freq.unused_indices):
            # choose first template at first occurrence
            chosen_index = 0
        '''

        if len(freq.unused_indices) != 0:
            # when there are non used templates left, choose one from them randomly
            chosen_index = random.choice(freq.unused_indices)
        else:
            # when every template is already used, choose one from all existing randomly except last used
            if len(possibilities) == 1:  # only one option
                chosen_index = 0
            else:
                possible_indices = []
                for i in range(len(possibilities)):   # extracting possible indices - every except the last_used
                    if i != freq.last_used:
                        possible_indices.append(i)
                chosen_index = random.choice(possible_indices)

        freq.last_used = chosen_index   # change last used to currently chosen
        freq.remove_from_unused_indices(chosen_index)   # update unused_indices
        return possibilities[chosen_index]

    def __get_template_frequency(self, id_: str) -> TemplateFrequency:
        """
        Returns wanted record from frequency table.
        :param id_: template's string id
        :return: TemplateFrequency
        """

        for f in self.frequency_table:
            if f.id == id_:
                return f

    @staticmethod
    def __get_msg_data(explicit_data: Types.ExplicitEntityData, msg: dp.Message):
        """
        Returns data (without specification of it's type), which are necessary to initialize entity template.
        :param explicit_data: Type of explicit data.
        :param msg: Message
        :return: some class from Data - Data.Player, Data.Time, etc.
        """

        if explicit_data == Types.ExplicitEntityData.PARTICIPANT:
            return msg.participant
        elif explicit_data == Types.ExplicitEntityData.PARTICIPANT_IN:
            return msg.participant_in
        elif explicit_data == Types.ExplicitEntityData.PARTICIPANT_OUT:
            return msg.participant_out
        elif explicit_data == Types.ExplicitEntityData.ASSISTANCE:
            return msg.assistance
        elif explicit_data == Types.ExplicitEntityData.TIME:
            return msg.time
        elif explicit_data == Types.ExplicitEntityData.SCORE:
            return msg.score
        elif explicit_data == Types.ExplicitEntityData.CURRENT_SCORE:
            return msg.current_score
        elif explicit_data == Types.ExplicitEntityData.TEAM_HOME:
            return msg.team_home
        elif explicit_data == Types.ExplicitEntityData.TEAM_AWAY:
            return msg.team_away
        else:
            pass


class Constituent:
    """Class to represent sentence constituent.
    After lexicalization and picking template for this constituent, it can result in more than one word."""
    id: str
    morph_params: MorphParams
    explicit_data: Types.ExplicitEntityData   # used just for entity constituents
    string: str   # lexicalized language specific expression

    def __init__(self, id_: str, morph_params: str, explicit_data: Types.ExplicitEntityData):
        self.id = id_
        self.morph_params = MorphParams.create(morph_params)
        self.explicit_data = explicit_data
        self.string = ''

    def lexicalize(self, msg: dp.Message, template_handler: TemplateHandler):
        """
        Lexicalizes constituent.
        :param msg: Message
        :param template_handler: TemplateHandler that will take care of picking suitable template
        """
        self.string = template_handler.get_template(self.id, self.explicit_data, msg).string

    def transform_string_for_geneea(self):
        """Transforms lexicalized string into Geneea input using it's morphological parameters."""
        self.string = MorphParams.apply_to_string(self.morph_params, self.string)


@dataclass
class Sentence:
    """Class to represent sentence."""
    id: str
    simple: bool
    constituents: List[Union[str, Constituent]]   # constituent can be string or class Constituent (later lexicalized)
    msg: dp.Message

    @staticmethod
    def create(type_: str, subtype: str, simple: bool, constituents: List[Union[str, Constituent]]):
        """
        Creates instance of the Sentence given it's attributes.
        :param type_: type of the sentence
        :param subtype: subtype of the sentence
        :param simple: bool flag that signalizes if structure of the sentence is simple (simple=True). Otherwise
        it signalizes that the structure or lexicalization is little bit more difficult.
        :param constituents: List of constituents of the sentence.
        :return: Sentence
        """
        id_ = Sentence.__init_sentence_id(type_, subtype)
        return Sentence(id=id_, simple=simple, constituents=constituents, msg=None)

    @staticmethod
    def __init_sentence_id(type_: str, subtype: str) -> str:
        """
        Combines type and subtype into sentence id.
        :param type_: type of the sentence
        :param subtype: subtype of the sentence
        :return: string id of the sentence
        """
        d = '-'
        if subtype != '':
            subtype = d + subtype
        return 's' + d + type_ + subtype

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def lexicalize(self, template_handler: TemplateHandler) -> str:
        """
        Lexicalizing whole sentence and also transforming strings into well-build Geneea input.
        :param template_handler: current Template handler
        :return: string for Geneea API
        """
        # lexicalizing every constituent of the sentence
        # using template handler to assign templates for constituents not randomly
        for c in self.constituents:
            if type(c) is Constituent:
                c.lexicalize(self.msg, template_handler)

        # transforming every constituent string for string version as correct Geneea input
        for c in self.constituents:
            if type(c) is Constituent:
                c.transform_string_for_geneea()

        return self.__combine_to_string()

    def __combine_to_string(self) -> str:
        """
        Combines every constituent of the sentence and creating one string.
        First letter of the sentence is upper case, spaces between constituents, point in the end of the sentence.
        :return: Sentence string.
        """
        words: List[str] = []
        for c in self.constituents:
            if type(c) is Constituent:
                words.append(c.string)
            else:
                words.append(c)

        # first letter is upper case
        i = 0
        while not words[0][i].isalpha() and i != len(words[0]):
            i += 1
        words[0] = words[0][:i] + words[0][i].upper() + words[0][i + 1:]

        return ' '.join(words) + '.'


class SentenceHandler:
    """
    Class for handling assigning and picking suitable sentences for messages.
    """
    sentences: List[Sentence]
    used_sentences: List[Sentence]

    def __init__(self):
        # when initializing new SentenceHandler we initialize all possible sentences
        self.sentences = SentenceHandler.__init_all_sentences()
        self.used_sentences = []

    def __find_next_simple(self, start_index: int) -> int:
        """
        In the list of all possible sentences (must be SORTED) we find next simple sentence of the same id.
        Since at least one simple exists for each sentence id, we have to find a sentence.
        :param start_index: index of sentences where to start the iteration for finding simple sentence
        :return: Index of the next simple sentence.
        """
        index = start_index
        while not self.sentences[index].simple:
            index += 1

        return index

    def __swap(self, index1: int, index2: int):
        """
        Swaps two sentences in sentence list given their indices.
        :param index1: Index of the first sentence to swap.
        :param index2: Index of the second sentence to swap.
        """
        tmp = self.sentences[index1]
        self.sentences[index1] = self.sentences[index2]
        self.sentences[index2] = tmp

    def __skip_to_next_sentence_type(self, start_index: int) -> int:
        """
        Looping through sentences of the same id until new id of the sentence is found.
        :param start_index:  Start index of the list of sentences.
        :return: Index where the same sentence id ends.
        """
        index = start_index
        while index + 1 < len(self.sentences) and self.sentences[index] == self.sentences[index + 1]:
            index += 1
        return index + 1

    def __put_simple_first(self):
        """Ensures to put simple version of the sentence first for every sentence id."""
        index = 0
        while index + 1 < len(self.sentences):
            if not self.sentences[index].simple:    # if there is not simple version already on the first index
                simple_index = self.__find_next_simple(index)
                self.__swap(index, simple_index)
            index = self.__skip_to_next_sentence_type(index)

    def __randomize_sentences_order(self):
        """Randomizes order of the sentences following certain rules."""
        random.shuffle(self.sentences)    # shuffle sentences to make sure sentences order will vary
        self.sentences.sort()             # sort sentences so that they are grouped by id
        self.__put_simple_first()           # put simple version first for every sentence id group

    @staticmethod
    def __init_all_sentences():
        """Initializes all sentences."""
        def __init_sentence_result():
            """Initializes all sentences for expressing result message."""
            type_ = 'r'
            # id subtypes: win = 'w' / draw = 'd' / loss = 'l'

            # win
            subtype = 'w'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-win', morph_params='.-0-.-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='4-.-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

            # draw
            subtype = 'd'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-draw', morph_params='.-0-.-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='7-.-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

            # lose
            subtype = 'l'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-lose', morph_params='.-0-.-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='4-.-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

        def __init_sentence_goal():
            """Initializes all sentences for expressing goal message."""
            type_ = 'g'
            # id subtypes: solo play = 's' / own goal = 'o' / penalty = 'p' / assistance = 'a'

            # Types.Goal.SOLO_PLAY
            subtype = 's'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                'po',
                Constituent(id_='w-nice', morph_params='6-.-.-.-1', explicit_data=None),
                Constituent(id_='w-action', morph_params='6-.-.-1-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                'po',
                Constituent(id_='w-nice', morph_params='6-.-.-.-1', explicit_data=None),
                Constituent(id_='w-action', morph_params='6-.-.-1-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None),
                'po',
                Constituent(id_='w-nice', morph_params='6-.-.-.-1', explicit_data=None),
                Constituent(id_='w-action', morph_params='6-.-.-1-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None),
                "a",
                Constituent(id_='v-score_change', morph_params='.-0-.-.-.', explicit_data=None),
                "na",
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.CURRENT_SCORE)]))

            # Types.Goal.ASSISTANCE
            subtype = 'a'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='2-.-0-.-.', explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='2-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='2-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                'po',
                Constituent(id_='w-nice', morph_params='6-.-.-.-1', explicit_data=None),
                Constituent(id_='w-action', morph_params='6-.-.-1-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='2-.-0-.-.', explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                'po',
                Constituent(id_='w-nice', morph_params='6-.-.-.-1', explicit_data=None),
                Constituent(id_='w-action', morph_params='6-.-.-1-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='2-.-0-.-.', explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='w-goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            # Types.Goal.PENALTY
            subtype = 'p'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-penalty', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-penalty', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-penalty', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-penalty', morph_params='4-.-.-.-.', explicit_data=None)]))

            # Types.Goal.OWN_GOAL
            subtype = 'o'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                "si dal",
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-own_goal', morph_params='4-.-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                "si dal nešťastně",
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-own_goal', morph_params='4-.-.-.-.', explicit_data=None)]))

        def __init_sentence_substitution():
            """Initializes all sentences for expressing substitution message."""
            type_ = 's'
            subtype = ''

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-substitution', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                "za",
                Constituent(id_='e-player', morph_params='4-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-substitution', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Constituent(id_='e-player', morph_params='4-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Constituent(id_='v-substitution', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='4-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Constituent(id_='v-substitution', morph_params='.-0-.-.-.', explicit_data=None),
                "za",
                Constituent(id_='e-player', morph_params='4-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Constituent(id_='v-substitution', morph_params='.-0-.-.-.', explicit_data=None),
                "za",
                Constituent(id_='e-player', morph_params='4-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME)]))

        def __init_sentence_card():
            """Initializes all sentences for expressing card message."""
            type_ = 'c'
            # id subtypes: red_auto = 'a' / red_instant = 'r' / yellow = 'y'

            # Types.Card.RED_AUTO
            subtype = 'a'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-red_card', morph_params='4-.-2-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-red_card', morph_params='4-.-2-.-.', explicit_data=None)]))

            # Types.Card.RED_INSTANT
            subtype = 'r'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po druhé žluté kartě",
                Constituent(id_='w-red_card', morph_params='4-.-2-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                "po druhé žluté kartě",
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-red_card', morph_params='4-.-2-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "druhou",
                Constituent(id_='w-yellow_card', morph_params='4-.-2-.-.', explicit_data=None),
                "a tím pro něj zápas skončil"]))

            # Types.Card.YELLOW
            subtype = 'y'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-yellow_card', morph_params='4-.-2-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-card', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-yellow_card', morph_params='4-.-2-.-.', explicit_data=None)]))

        def __init_sentence_missed_penalty():
            """Initializes all sentences for expressing missed penalty message."""
            type_ = 'm'
            subtype = ''

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='e-player', morph_params='1-.-0-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-failed_penalty', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='w-penalty', morph_params='', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-player', morph_params='1-.-0-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-failed_penalty', morph_params='.-0-.-.-.', explicit_data=None),
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='w-penalty', morph_params='', explicit_data=None)]))

        sentences: List[Sentence] = []

        __init_sentence_result()
        __init_sentence_goal()
        __init_sentence_substitution()
        __init_sentence_card()
        __init_sentence_missed_penalty()
        sentences.sort()
        return sentences

    def __try_find_sentence(self, id_: str) -> (bool, int):
        """
        Trying to find sentence in all sentences with a certain id.
        :param id_: String id of the sentence
        :return: Tuple of boolean an int - bool says if a sentence was found, int is the index
        (if found == False, then the index is useless)
        """
        for i in range(0, len(self.sentences)):
            if self.sentences[i].id == id_:
                return True, i

        return False, None

    def __get_random_used(self, id_: str) -> Sentence:
        """
        Returns random sentence with given id from already used sentences.
        :param id_: id of the sentence
        :return: Sentence
        """
        valid_sentences: List[Sentence] = []
        for us in self.used_sentences:
            if us.id == id_:
                valid_sentences.append(us)

        return random.choice(valid_sentences)

    def get_sentence(self, m: dp.Message) -> Sentence:
        """
        Picks suitable sentence given the message.
        :param m: Message
        :return: Sentence
        """
        id_ = self.__init_sentence_id(m)
        (found, sentence_index) = self.__try_find_sentence(id_)

        if found:
            sentence = self.sentences.pop(sentence_index)
            sentence.msg = m
            self.used_sentences.append(sentence)
            return sentence
        else:
            sentence = copy.deepcopy(self.__get_random_used(id_))   # need a new object to dont ruin the previous one
            sentence.msg = m
            return sentence

    def create_sentences_templates(self, doc_plan: dp.DocumentPlan) -> (Sentence, List[Sentence]):
        """
        Picks suitable sentence for every message.
        Matches sentences with particular data from Message.
        :param doc_plan: DocumentPlan
        :return: Tuple of sentences - title(Sentence) and body (List[Sentence])
        """
        self.__randomize_sentences_order()   # randomizing sentence order (but sorted)
        title_sentence = self.get_sentence(doc_plan.title)
        body_sentences = [self.get_sentence(msg) for msg in doc_plan.body]
        return title_sentence, body_sentences

    @staticmethod
    def __init_sentence_id(m: dp.Message) -> str:
        """
        Creates string id from Message.
        :param m: Message.
        :return: Sentence id
        """
        d = '-'
        s = 's' + d

        subtype = ''
        if type(m) is dp.Message.Result:
            type_ = 'r'
            if m.score.result == Types.Result.WIN:
                subtype = 'w'
            elif m.score.result == Types.Result.DRAW:
                subtype = 'd'
            else:  # Types.Result.LOSE
                subtype = 'l'
        elif type(m) is dp.Message.Goal:
            type_ = 'g'
            if m.goal_type == Types.Goal.SOLO_PLAY:
                subtype = 's'
            elif m.goal_type == Types.Goal.ASSISTANCE:
                subtype = 'a'
            elif m.goal_type == Types.Goal.OWN_GOAL:
                subtype = 'o'
            else:  # Types.Goal.PENALTY
                subtype = 'p'
        elif type(m) is dp.Message.Substitution:
            type_ = 's'
        elif type(m) is dp.Message.Card:
            type_ = 'c'
            if m.card_type == Types.Card.RED_AUTO:
                subtype = 'a'
            elif m.card_type == Types.Card.RED_INSTANT:
                subtype = 'r'
            else:  # Types.Card.YELLOW
                subtype = 'y'
        else:  # type(m) is dp.Message.MissedPenalty:
            type_ = 'm'

        if subtype == '':
            s += type_
        else:
            s += type_ + d + subtype

        return s


class SentencePlanner:
    """Class to transform document plan in the form of messages to text,
    which is then transformed into well-build input for Geneea API."""
    @staticmethod
    def lexicalize_article(doc_plan: dp.DocumentPlan, match_data: Data.Match) -> (str, List[str]):
        """
        Core method for lexicalizing given document plan and transforming lexicalized text for well-build Geneea input.
        :param doc_plan: Document Plan
        :param match_data: other match data (if needed for some conditional expression)
        :return:returns (str, List[str]) so that first of the tuple is title and rest is body
        of the article. All strings are well-build inputs for Geneea API.
        """

        # creating sentences templates using SentenceHandler
        sh: SentenceHandler = SentenceHandler()
        (title_sentence, body_sentences) = sh.create_sentences_templates(doc_plan)

        # creating templates for each of the sentence constituent using TemplateHandler
        th: TemplateHandler = TemplateHandler()
        title = title_sentence.lexicalize(th)
        body = [sentence.lexicalize(th) for sentence in body_sentences]

        return title, body
