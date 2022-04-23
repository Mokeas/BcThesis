"""Lexicalize document plan with specific language expressions and
also transforming lexicalized text into valid input for Geneea.
Input is document plan and match data, output is string that can be an input of Geneea API.
"""

# Python's libraries
import random
from typing import List, Tuple, Union
from dataclasses import dataclass
# Other parts of the code
import Types
import document_planner as dp
import Data


@dataclass(frozen=True)
class MorphParams:
    """Class to transform linguistic requirements into Geneea well-build input. """
    case: Types.Morph.Case
    tense: Types.Morph.Tense
    ref: None
    agr: None

    @staticmethod
    def create(string_id: str):
        params: (Types.Morph.Case, Types.Morph.Tense, str, str) = MorphParams.get_morph_params(string_id)
        return MorphParams(case=params[0], tense=params[1], ref=params[2], agr=params[3])

    @staticmethod
    def get_morph_params(string_id: str) -> (Types.Morph.Case, Types.Morph.Tense, str, str):
        """Transforms string into morphological attributes.
        String_id is in form case-tense-ref-afr and . is used to blank attribute.
        """
        if string_id == '':
            return None, None, None, None
        else:
            [case_id, tense_id, ref_id, agr_id] = string_id.split('-')

            # . stands for non-defined parameter
            case = None if case_id == "." else Types.Morph.Case(int(case_id))
            tense = None if tense_id == "." else Types.Morph.Tense(int(tense_id))
            ref = None if ref_id == "." else ref_id
            agr = None if agr_id == "." else agr_id

            return case, tense, ref, agr

    def apply_to_string(self, constituent: str) -> str:
        """Takes constituent and applies given attributes. Output is well-build string for Geneea API interface."""
        header = '{{' + f'\'{constituent}\'|morph('

        mp: List[str] = []
        all_none = True

        if self.case is not None:
            mp.append(f'\'Case={MorphParams.to_valid_form(self.case.name)}\'')
            all_none = False

        if self.tense is not None:
            mp.append(f'\'Tense={MorphParams.to_valid_form(self.tense.name)}\'')
            all_none = False

        if self.ref is not None:
            mp.append(f'ref={self.ref}')
            all_none = False

        if self.agr is not None:
            mp.append(f'ref={self.agr}')
            all_none = False

        body = ", ".join(mp)

        return constituent if all_none else header + body + ')}}'

    @staticmethod
    def to_valid_form(s: str) -> str:
        return s.lower().capitalize()


@dataclass
class TemplateFrequency:
    """Class to store frequency of every template according to it's string id."""
    id: str
    count: int
    unused_indices: List[int]   # indices of templates that haven't been used yet
    last_used: int

    @staticmethod
    def create(id_: str, count: int):
        unused_indices = [i for i in range(count)]
        return TemplateFrequency(id=id_, count=count, unused_indices=unused_indices, last_used=-1)

    def remove_from_unused_indices(self, chosen_index: int):
        """Removes index from unused indices after using this particular template."""
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
    def create(type_: str, subtype: str, string: str):   # creating will create immutable template
        id_ = Template.create_template_id(type_, subtype)
        return Template(id_, string)

    @staticmethod
    def create_template_id(type_: str, subtype: str):
        """Transforms type and subtype into string id of the template."""
        return type_ + '-' + subtype

    def __str__(self):
        return '[id: ' + self.id + ' | string: ' + self.string + "]"


class TemplateHandler:
    """Class for handling template choices systematically.
    Stores information about used templates in frequency table,
    which is a list of the auxiliary TemplateFrequency class.
    """
    frequency_table: List[TemplateFrequency]

    def __init__(self):
        """Initializing frequency table attribute."""
        # creating every template possible
        all_templates = TemplateHandler._init_all_templates()
        # initializing frequency table from all possible templates
        self.frequency_table = TemplateHandler._init_frequency_table(all_templates)

    @staticmethod
    def _init_all_templates() -> List[Template]:
        """Initializes every template that could be used."""
        templates_entities = TemplateHandler.get_templates_entity(first_init=True, subtype='', data=None)
        templates_words = TemplateHandler.get_templates_word(first_init=True, subtype='')
        templates_verbs = TemplateHandler.get_templates_verb(first_init=True, subtype='')
        return templates_entities + templates_verbs + templates_words

    @staticmethod
    def _init_frequency_table(all_templates: List[Template]) -> List[TemplateFrequency]:
        """Initializes frequency table using all templates possible."""
        index = 0
        frequency_table: List[TemplateFrequency] = []

        # no sorting is needed since Template initializing is systematically
        while index + 1 < len(all_templates):
            (end_index, count) = TemplateHandler.proceed_to_next_template_type(all_templates, index)
            frequency_table.append(TemplateFrequency.create(all_templates[index].id, count))
            index += 1

        return frequency_table

    @staticmethod
    def proceed_to_next_template_type(all_templates: List[Template], start_index: int) -> (int, int):
        """Looping through templates of the same id.
        Takes list of all templates and starting index of the template to count frequency for.
        Returns tuple of ints - index where the same id template ends, count of the template.
        """
        index = start_index
        count = 1
        while index + 1 < len(all_templates) and all_templates[index].id == all_templates[index+1].id:
            index += 1
            count += 1

        return index, count

    @staticmethod
    def get_templates_entity(first_init: bool, subtype: str, data) -> List[Template]:
        """Creates entity templates. Takes three arguments:
        1) bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        2) subtype (e.g. 'goal').
        3) data - correct data entity (e.g. for initializing it is Data.Player, for time Data.Time, etc.).
        """
        def init_time_templates():
            """Auxiliary function to create time templates."""
            entity_type = 'time'
            time: Data.Time = data

            if first_init:
                time = Data.Time.create(0, 0)    # creating random time for first_init

            if time.added != 0:  #
                if time.base == 45:  # first half
                    templates.append(Template.create(type_, entity_type,
                                                     f"v {time.added if data is not None else ''}"
                                                     f". minutě nastavení prvního poločasu"))
                    templates.append(('e-time-2', f"{time.added} minuty po začátku nastaveného času prvního poločasu"))
                else:  # second half
                    templates.append(Template.create(type_, entity_type,
                                                     f"v {time.added if data is not None else ''}"
                                                     f". minutě nastavení druhého poločasu"))
                    templates.append(('e-time-2', f"{time.added} minuty po začátku nastaveného času druhého poločasu"))
            else:
                templates.append(Template.create(type_, entity_type,
                                                 f"v {time.base if data is not None else ''}. minutě"))
                templates.append(('e-time-2', f"{time.base} minuty po začátku"))

        def init_player_templates():
            """Auxiliary function to create player templates."""
            entity_type = 'player'
            player: Data.Player = data

            templates.append(Template.create(type_, entity_type,
                                             player.full_name if data is not None else ''))
            templates.append(Template.create(type_, entity_type,
                                             player.get_last_name() if data is not None else ''))
            templates.append(Template.create(type_, entity_type,
                                             f"hráč s číslem {player.number if data is not None else ''}"))

        def init_team_templates():
            """Auxiliary function to create team templates."""
            entity_type = 'team'
            team: Data.Team = data

            templates.append(Template.create(type_, entity_type,
                                             team.name if data is not None else ''))

        def init_score_templates():
            """Auxiliary function to create score templates."""
            entity_type = 'score'
            score: Data.Score = data

            templates.append(Template.create(type_, entity_type,
                                             f"{score.goals_home if data is not None else ''}:"
                                             f"{score.goals_away if data is not None else ''}"))

        type_ = 'e'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            init_time_templates()
            init_player_templates()
            init_team_templates()
            init_score_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'time':
            init_time_templates()
        elif subtype == 'player':
            init_player_templates()
        elif subtype == 'team':
            init_team_templates()
        elif subtype == 'score':
            init_score_templates()
        else:
            print("Type Unknown")

        return templates

    @staticmethod
    def get_templates_word(first_init: bool, subtype: str) -> List[Template]:
        """Creates word templates. Takes two arguments:
        1) bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        2) subtype (e.g. 'penalty').
        """

        def init_goal_templates():
            """Auxiliary function to create goal templates."""
            word_type = 'goal'
            templates.append(Template.create(type_, word_type, 'gól'))
            templates.append(Template.create(type_, word_type, 'branka'))

        def init_assistance_templates():
            """Auxiliary function to create assistance templates."""
            word_type = 'assistance'
            templates.append(Template.create(type_, word_type, 'asistence'))
            templates.append(Template.create(type_, word_type, 'nahrávka'))
            templates.append(Template.create(type_, word_type, 'přihrávka'))
            templates.append(Template.create(type_, word_type, 'pas'))

        def init_penalty_templates():
            """Auxiliary function to create penalty templates."""
            word_type = 'penalty'
            templates.append(Template.create(type_, word_type, 'penalta'))
            templates.append(Template.create(type_, word_type, 'pokutový kop'))
            templates.append(Template.create(type_, word_type, 'jedenáctka'))

        def init_own_goal_templates():
            """Auxiliary function to create own goal templates."""
            word_type = 'own_goal'
            templates.append(Template.create(type_, word_type, 'vlastňák'))
            templates.append(Template.create(type_, word_type, 'vlastní gól'))
            templates.append(Template.create(type_, word_type, 'vlastenec'))

        def init_yellow_card_templates():
            """Auxiliary function to create yellow card templates."""
            word_type = 'yellow_card'
            templates.append(Template.create(type_, word_type, 'žlutá'))
            templates.append(Template.create(type_, word_type, 'žlutá karta'))

        def init_red_card_templates():
            """Auxiliary function to create red card templates."""
            word_type = 'red_card'
            templates.append(Template.create(type_, word_type, 'červená'))
            templates.append(Template.create(type_, word_type, 'červená karta'))

        def init_result_draw_templates():
            """Auxiliary function to create result(draw) templates."""
            word_type = 'draw'
            templates.append(Template.create(type_, word_type, 'remíza'))
            templates.append(Template.create(type_, word_type, 'plichta'))
            templates.append(Template.create(type_, word_type, 'nerozhodný výsledek'))

        def init_result_lose_templates():
            """Auxiliary function to create result(lose) templates."""
            word_type = 'lose'
            templates.append(Template.create(type_, word_type, 'porážka'))
            templates.append(Template.create(type_, word_type, 'prohra'))
            templates.append(Template.create(type_, word_type, 'debakl'))
            templates.append(Template.create(type_, word_type, 'ostuda'))

        def init_result_win_templates():
            """Auxiliary function to create result(win) templates."""
            word_type = 'win'
            templates.append(Template.create(type_, word_type, 'vítězství'))
            templates.append(Template.create(type_, word_type, 'výhra'))
            templates.append(Template.create(type_, word_type, 'zdar'))

        type_ = 'w'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            init_goal_templates()
            init_assistance_templates()
            init_penalty_templates()
            init_own_goal_templates()
            init_yellow_card_templates()
            init_red_card_templates()
            init_result_draw_templates()
            init_result_lose_templates()
            init_result_win_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'goal':
            init_goal_templates()
        elif subtype == 'assistance':
            init_assistance_templates()
        elif subtype == 'penalty':
            init_penalty_templates()
        elif subtype == 'own_goal':
            init_own_goal_templates()
        elif subtype == 'yellow_card':
            init_red_card_templates()
        elif subtype == 'red_card':
            init_assistance_templates()
        elif subtype == 'draw':
            init_result_draw_templates()
        elif subtype == 'lose':
            init_result_lose_templates()
        elif subtype == 'win':
            init_result_win_templates()
        else:
            pass

        return templates

    @staticmethod
    def get_templates_verb(first_init: bool, subtype: str) -> List[Template]:
        """Creates verb templates. Takes two arguments:
        1) bool value if it is first initialization - if True, initialize every single entity template.
        (and also the rest of the arguments are then irrelevant)
        2) subtype (e.g. 'penalty').
        """
        def init_result_win_templates():
            """Auxiliary function to create win templates."""
            verb_type = 'win'
            templates.append(Template.create(type_, verb_type, 'porazit'))
            templates.append(Template.create(type_, verb_type, 'rozdrtit'))
            templates.append(Template.create(type_, verb_type, 'deklasovat'))

        def init_result_draw_templates():
            """Auxiliary function to create draw templates."""
            verb_type = 'draw'
            templates.append(Template.create(type_, verb_type, 'remizovat'))

        def init_result_lose_templates():
            """Auxiliary function to create lose templates."""
            verb_type = 'lose'
            templates.append(Template.create(type_, verb_type, 'prohrát'))

        def init_goal_templates():
            """Auxiliary function to create goal templates."""
            verb_type = 'goal'
            templates.append(Template.create(type_, verb_type, 'vstřelit'))
            templates.append(Template.create(type_, verb_type, 'vsítit'))
            templates.append(Template.create(type_, verb_type, 'dát'))

        def init_score_change_templates():
            """Auxiliary function to create change of score templates."""
            verb_type = 'score_change'
            templates.append(Template.create(type_, verb_type, 'změnil'))
            templates.append(Template.create(type_, verb_type, 'upravilt'))
            templates.append(Template.create(type_, verb_type, 'zvýšil'))

        def init_penalty_templates():
            """Auxiliary function to create penalty templates."""
            verb_type = 'penalty'
            templates.append(Template.create(type_, verb_type, 'proměnit'))
            templates.append(Template.create(type_, verb_type, 'dát'))

        def init_failed_penalty_templates():
            """Auxiliary function to create failed penalty templates."""
            verb_type = 'failed_penalty'
            templates.append(Template.create(type_, verb_type, 'zpackat'))
            templates.append(Template.create(type_, verb_type, 'neproměnit'))
            templates.append(Template.create(type_, verb_type, 'nedat'))

        def init_substitution_templates():
            """Auxiliary function to create substitution templates."""
            verb_type = 'substitution'
            templates.append(Template.create(type_, verb_type, 'střídat'))
            templates.append(Template.create(type_, verb_type, 'vystřídat'))

        def init_card_templates():
            """Auxiliary function to create card templates."""
            verb_type = 'card'
            templates.append(Template.create(type_, verb_type, 'dostat'))
            templates.append(Template.create(type_, verb_type, 'obdržet'))
            templates.append(Template.create(type_, verb_type, 'vyfasovat'))

        type_ = 'v'
        templates: List[Template] = []

        if first_init:   # initializing every template when first init
            init_result_win_templates()
            init_result_draw_templates()
            init_result_lose_templates()
            init_goal_templates()
            init_score_change_templates()
            init_penalty_templates()
            init_failed_penalty_templates()
            init_substitution_templates()
            init_card_templates()
            return templates

        # initializing only templates needed for given subtype
        if subtype == 'win':
            init_result_win_templates()
        elif subtype == 'draw':
            init_result_draw_templates()
        elif subtype == 'lose':
            init_result_lose_templates()
        elif subtype == 'goal':
            init_goal_templates()
        elif subtype == 'score_change':
            init_score_change_templates()
        elif subtype == 'penalty':
            init_penalty_templates()
        elif subtype == 'failed_penalty':
            init_failed_penalty_templates()
        elif subtype == 'substitution':
            init_substitution_templates()
        elif subtype == 'card':
            init_card_templates()
        else:
            pass

        return templates

    @staticmethod
    def get_possible_templates(id_: str, explicit_data: Types.ExplicitEntityData, msg: dp.Message) -> List[Template]:
        """Returns list to all possible templates given template id, data type and message."""
        constituent_type: str = id_.split('-')[0]
        subtype: str = id_.split('-')[1]
        possibilities: List[Template] = []

        if constituent_type == 'e':  # ENTITY
            # data variable only used when const_type is entity
            data = TemplateHandler.get_msg_data(explicit_data, msg)
            possibilities = TemplateHandler.get_templates_entity(first_init=False, subtype=subtype, data=data)
        elif constituent_type == 'w':  # WORD
            possibilities = TemplateHandler.get_templates_word(first_init=False, subtype=subtype)
        elif constituent_type == 'v':  # VERB
            possibilities = TemplateHandler.get_templates_verb(first_init=False, subtype=subtype)
        else:
            pass

        return possibilities

    def get_template(self, id_: str, explicit_data: Types.ExplicitEntityData, msg: dp.Message) -> Template:
        """Picking template for given constituent information - id, data, message."""
        possibilities = TemplateHandler.get_possible_templates(id_, explicit_data, msg)
        chosen_template = self.choose_template(possibilities)
        return chosen_template

    def choose_template(self, possibilities: List[Template]) -> Template:
        """Chooses template from all possible templates using this algorithm:
        1) if we haven't used every template - pick one randomly
        2) if we already used every template once - pick randomly from every template possible
        (except the last used so that ensure some differentiation.
        """
        id_ = possibilities[0].id
        freq: TemplateFrequency = self._get_template_frequency(id_)
        chosen_index = -1   # variable initialization - value will change in if else

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

    def _get_template_frequency(self, id_: str) -> TemplateFrequency:
        """Returns TemplateFrequency from frequency table given it's id."""
        for f in self.frequency_table:
            if f.id == id_:
                return f

    @staticmethod
    def get_msg_data(explicit_data: Types.ExplicitEntityData, msg: dp.Message):
        """According to explicit_data type returns data (without specification of it's type),
        which are necessary to initialize entity template.
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
    id: str
    morph_params: MorphParams
    explicit_data: Types.ExplicitEntityData
    string: str

    def __init__(self, id_: str, morph_params: str, explicit_data: Types.ExplicitEntityData):
        self.id = id_
        self.morph_params = MorphParams.create(morph_params)
        self.explicit_data = explicit_data
        self.string = ''

    def lexicalize(self, msg: dp.Message, template_handler: TemplateHandler):
        self.string = template_handler.get_template(self.id, self.explicit_data, msg).string

    def transform_string_for_geneea(self):
        self.string = MorphParams.apply_to_string(self.morph_params, self.string)


@dataclass
class Sentence:
    id: str
    simple: bool
    constituents: List[Union[str, Constituent]]
    msg: dp.Message

    @staticmethod
    def create(type_: str, subtype: str, simple: bool, constituents: List[Union[str, Constituent]]):
        id_ = Sentence._init_sentence_id(type_, subtype)
        return Sentence(id=id_, simple=simple, constituents=constituents, msg=None)

    @staticmethod
    def _init_sentence_id(type_: str, subtype: str) -> str:
        d = '-'
        if subtype != '':
            subtype = d + subtype
        return 's' + d + type_ + subtype

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def lexicalize(self, template_handler: TemplateHandler) -> str:
        for c in self.constituents:
            if type(c) is Constituent:
                c.lexicalize(self.msg, template_handler)

        for c in self.constituents:
            if type(c) is Constituent:
                c.transform_string_for_geneea()

        return self.combine_to_string()

    def combine_to_string(self) -> str:
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
    sentences: List[Sentence]
    used_sentences: List[Sentence]

    def __init__(self):
        self.sentences = SentenceHandler.init_all_sentences()
        self.used_sentences = []

    '''
     def update_sentence_frequency(self, start_index: int) -> int:
        index = start_index
        count = 1
        while index + 1 < len(self.sentences) and self.sentences[index].id == self.sentences[index+1].id:
            count += 1
            index += 1

        for i in range(start_index, index+1):
            self.sentences[i].frequency = count

        return index

    def init_sentences_count(self):
        curr_index = 0
        while curr_index < len(self.sentences):
            curr_index = self.update_sentence_frequency(curr_index)
            curr_index += 1
    '''

    def skip_to_next_simple(self, start_index: int) -> int:
        index = start_index
        while not self.sentences[index].simple:
            index += 1

        return index

    def swap_two_elements(self, index1: int, index2: int):
        tmp = self.sentences[index1]
        self.sentences[index1] = self.sentences[index2]
        self.sentences[index2] = tmp

    def skip_to_next_sentence_type(self, start_index: int) -> int:
        index = start_index
        while index + 1 < len(self.sentences) and self.sentences[index] == self.sentences[index + 1]:
            index += 1
        return index + 1

    def put_simple_first(self):
        index = 0
        while index + 1 < len(self.sentences):
            if not self.sentences[index].simple:
                simple_index = self.skip_to_next_simple(index)
                self.swap_two_elements(index, simple_index)
            index = self.skip_to_next_sentence_type(index)

    def randomize_sentences_order(self):
        random.shuffle(self.sentences)
        self.sentences.sort()
        self.put_simple_first()

    @staticmethod
    def init_all_sentences():
        def init_sentence_result():
            type_ = 'r'
            # id subtypes: win = 'w' / draw = 'd' / loss = 'l'

            # win
            subtype = 'w'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-win', morph_params='.-0-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

            # draw
            subtype = 'd'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-draw', morph_params='.-0-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='7-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

            # lose
            subtype = 'l'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Constituent(id_='v-loss', morph_params='.-0-.-1', explicit_data=None),
                Constituent(id_='e-team', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.SCORE)]))

        def init_sentence_goal():
            type_ = 'g'
            # id subtypes: solo play = 's' / own goal = 'o' / penalty = 'p' / assistance = 'a'

            # Types.Goal.SOLO_PLAY
            subtype = 's'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.', explicit_data=None)]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-goal', morph_params='4-.-.-.', explicit_data=None),
                "a",
                Constituent(id_='v-score_change', morph_params='', explicit_data=None),
                "na",
                Constituent(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.CURRENT_SCORE)]))

            # Types.Goal.ASSISTANCE
            subtype = 'a'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po",
                Constituent(id_='w-assistance', morph_params='6-.-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='3-.-.-.', explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Constituent(id_='w-goal', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Goal.PENALTY
            subtype = 'p'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-penalty', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-penalty', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Goal.OWN_GOAL
            subtype = 'o'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                "si dal",
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-own_goal', morph_params='4-.-.-.', explicit_data=None)]))

        def init_sentence_substitution():
            type_ = 's'
            subtype = ''

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-substitution', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                "za",
                Constituent(id_='e-player', morph_params='4-.-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-substitution', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Constituent(id_='e-player', morph_params='4-.-.-.',
                            explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

        def init_sentence_card():
            type_ = 'c'
            # id subtypes: red_auto = 'a' / red_instant = 'r' / yellow = 'y'

            # Types.Card.RED_AUTO
            subtype = 'a'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-red_card', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Card.RED_INSTANT
            subtype = 'r'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "po druhé žluté kartě červenou"]))

            sentences.append(Sentence.create(type_, subtype, False, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                "druhou",
                Constituent(id_='w-yellow_card', morph_params='4-.-.-.', explicit_data=None),
                "a tím pro něj zápas skončil"]))

            # Types.Card.YELLOW
            subtype = 'y'
            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='w-yellow_card', morph_params='4-.-.-.', explicit_data=None)]))

        def init_sentence_missed_penalty():
            type_ = 'm'
            subtype = ''

            sentences.append(Sentence.create(type_, subtype, True, [
                Constituent(id_='e-time', morph_params='', explicit_data=Types.ExplicitEntityData.TIME),
                Constituent(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT),
                Constituent(id_='v-failed_penalty', morph_params='.-0-.-.', explicit_data=None),
                Constituent(id_='w-penalty', morph_params='', explicit_data=None)]))

        sentences: List[Sentence] = []

        init_sentence_result()
        init_sentence_goal()
        init_sentence_substitution()
        init_sentence_card()
        init_sentence_missed_penalty()
        sentences.sort()
        return sentences

    def try_find_sentence(self, key: str) -> (bool, int):
        for i in range(0, len(self.sentences)):
            if self.sentences[i].id == key:
                return True, i

        return False, None

    def get_random_used(self, key: str) -> Sentence:
        valid_sentences: List[Sentence] = []
        for us in self.used_sentences:
            if us.id == key:
                valid_sentences.append(us)

        return random.choice(valid_sentences)

    def get_sentence(self, m: dp.Message) -> Sentence:
        key = self._init_sentence_key(m)
        (found, sentence_index) = self.try_find_sentence(key)

        if found:
            sentence = self.sentences.pop(sentence_index)
            sentence.msg = m
            self.used_sentences.append(sentence)
            return sentence
        else:
            sentence = self.get_random_used(key)
            sentence.msg = m
            return sentence

    def create_sentences_templates(self, doc_plan: dp.DocumentPlan) -> (Sentence, List[Sentence]):
        self.randomize_sentences_order()
        title_sentence = self.get_sentence(doc_plan.title)
        body_sentences = [self.get_sentence(msg) for msg in doc_plan.body]
        return title_sentence, body_sentences

    @staticmethod
    def _init_sentence_key(m: dp.Message) -> str:
        d = '-'
        s = 's' + d

        subtype = ''
        if type(m) is dp.Messages.Result:
            type_ = 'r'
            if m.score.result == Types.Result.WIN:
                subtype = 'w'
            elif m.score.result == Types.Result.DRAW:
                subtype = 'd'
            else:  # Types.Result.DRAW
                subtype = 'l'
        elif type(m) is dp.Messages.Goal:
            type_ = 'g'
            if m.goal_type == Types.Goal.SOLO_PLAY:
                subtype = 's'
            elif m.goal_type == Types.Goal.ASSISTANCE:
                subtype = 'a'
            elif m.goal_type == Types.Goal.OWN_GOAL:
                subtype = 'o'
            else:  # Types.Goal.PENALTY
                subtype = 'p'
        elif type(m) is dp.Messages.Substitution:
            type_ = 's'
        elif type(m) is dp.Messages.Card:
            type_ = 'c'
            if m.card_type == Types.Card.RED_AUTO:
                subtype = 'a'
            elif m.card_type == Types.Card.RED_INSTANT:
                subtype = 'r'
            else:  # Types.Card.YELLOW
                subtype = 'y'
        else:  # type(m) is dp.Messages.MissedPenalty:
            type_ = 'm'

        if subtype == '':
            s += type_
        else:
            s += type_ + d + subtype

        return s


class Lexicalizer:
    """Class to transform document plan in the form of messages to text,
    which is then transformed into well-build input for Geneea API."""
    @staticmethod
    def lexicalize_article(doc_plan: dp.DocumentPlan, match_data: Data.Match) -> (str, List[str]):
        """Core method for lexicalizing given document plan.
        Takes document plan and returns (str, List[str]) so that first of the tuple is title and rest is body
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
