# Brief description:

# lexicalize document plan with specific language expressions
# also transforming lexicalized text into valid input for Geneea
# input: DocumentPlan, Data.Match
# output: (str, List[str])

# -----------------------------------------------------
# Python's libraries
import random
from typing import List, Tuple, Union
# Other parts of the code
import Types
import document_planner as DP
import Data
# -----------------------------------------------------


class MorphParams:
    case: Types.Morph.Case
    tense: Types.Morph.Tense
    ref: None
    agr: None

    def __init__(self, string_id: str):
        params = MorphParams.get_morph_params(string_id)
        self.case = params[0]
        self.tense = params[1]
        self.ref = params[2]
        self.agr = params[3]

    @staticmethod
    def get_morph_params(string_id: str) -> (Types.Morph.Case, Types.Morph.Tense, str, str):
        if string_id == '':
            return None, None, None, None
        else:
            [case_id, tense_id, ref_id, agr_id] = string_id.split('-')

            case = None if case_id == "." else Types.Morph.Case(int(case_id))
            tense = None if tense_id == "." else Types.Morph.Tense(int(tense_id))
            ref = None if ref_id == "." else ref_id
            agr = None if agr_id == "." else agr_id

            return case, tense, ref, agr

    def apply_morph_params_to_string(self, constituent: str) -> str:
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


class Template:
    id: str
    msg: DP.Message
    morph_params: MorphParams
    data: None
    string: str

    def __init__(self, id: str, msg: DP.Message, morph_params: str, data, string):
        self.id = id
        self.msg = msg
        self.morph_params = MorphParams(morph_params)
        self.data = data
        self.string = string

    def lexicalize(self):
        constituent_type = self.id.split('-')[0]
        possibilities: List[Tuple[str, str]] = []

        if constituent_type == 'e':  # ENTITY
            possibilities = Template.get_string_poss_entity(self)
        elif constituent_type == 'w':  # WORD
            word_type = self.id.split('-')[1]
            possibilities = Template.get_string_poss_word(word_type)
        elif constituent_type == 'v':  # VERB
            verb_type = self.id.split('-')[1]
            possibilities = Template.get_string_poss_verb(verb_type)

        (new_id, new_string) = Template.get_random_poss(possibilities)

        self.id = new_id
        self.string = new_string

    def get_string_poss_entity(self) -> List[Tuple[str, str]]:
        def init_time_templates():
            time: Data.Time = self.data
            if time.added != 0:  #
                if time.base == 45:  # first half
                    templates.append(('e-time-1', f"v {time.added}. minutě nastavení prvního poločasu"))
                    # templates.append(('e-time-2', f"{time.added} minuty po začátku nastaveného času prvního poločasu"))
                else:  # second half
                    templates.append(('e-time-1', f"v {time.added}. minutě nastavení druhého poločasu"))
                    # templates.append(('e-time-2', f"{time.added} minuty po začátku nastaveného času druhého poločasu"))
            else:
                templates.append(('e-time-1', f"v {time.base}. minutě"))
                # templates.append(('e-time-2', f"{time.base} minuty po začátku"))

        # ToDo -> zaloznik/utocnik/obrance
        def init_player_templates():
            player: Data.Player = self.data
            templates.append(('e-player-1', player.full_name))
            templates.append(('e-player-2', player.get_last_name()))
            templates.append(('e-player-3', f"hráč s číslem {player.number}"))

        def init_team_templates():
            team: Data.Team = self.data
            templates.append(('e-team-1', team.name))

        def init_score_templates():
            score: Data.Score = self.data
            templates.append(('e-score-1', f"{score.goals_home}:{score.goals_away}"))

        templates: List[(str, str)] = []

        ent = self.id.split('-')[1]
        if ent == 'time':
            init_time_templates()
        elif ent == 'player':
            init_player_templates()
        elif ent == 'team':
            init_team_templates()
        elif ent == 'score':
            init_score_templates()
        else:
            print("Type Unknown")

        return templates

    @staticmethod
    def get_string_poss_word(word_type: str) -> List[Tuple[str, str]]:
        def init_word_templates():
            # goal
            templates.append(('w-goal-1', 'gól'))
            templates.append(('w-goal-2', 'branka'))

            # assistance
            templates.append(('w-assistance-1', 'asistence'))
            templates.append(('w-assistance-2', 'nahrávka'))

            # penalty
            templates.append(('w-penalty-1', 'penalta'))
            templates.append(('w-penalty-2', 'pokutový kop'))

            # own goal
            templates.append(('w-own_goal-1', 'vlastňák'))
            templates.append(('w-own_goal-2', 'vlastní gól'))

            # yellow card
            templates.append(('w-yellowcard-1', 'žlutá'))
            templates.append(('w-yellowcard-2', 'žlutá karta'))

            # red card
            templates.append(('w-redcard-1', 'červená'))
            templates.append(('w-redcard-2', 'červená karta'))

        templates: List[(str, str)] = []
        init_word_templates()
        return [t for t in templates if t[0].split('-')[1] == word_type]

    @staticmethod
    def get_string_poss_verb(verb_type: str) -> List[Tuple[str, str]]:
        def init_verb_templates():
            # result
            templates.append(('v-win-1', 'porazit'))
            templates.append(('v-win-2', 'rozdrtit'))
            templates.append(('v-win-3', 'deklasovat'))
            templates.append(('v-draw-1', 'remizovat'))
            templates.append(('v-loss-1', 'prohrát'))

            # goal
            templates.append(('v-goal-1', 'vstřelit'))
            templates.append(('v-goal-2', 'vsítit'))
            templates.append(('v-goal-3', 'dát'))

            # score change

            templates.append(('v-score_change-1', 'změnil'))
            templates.append(('v-score_change-2', 'upravil'))

            # penalty

            templates.append(('v-penalty-1', 'proměnit'))
            templates.append(('v-penalty-2', 'dát'))

            # failed penalty
            templates.append(('v-failed_penalty-1', 'zpackat'))
            templates.append(('v-failed_penalty-2', 'neproměnit'))
            templates.append(('v-failed_penalty-3', 'nedat'))

            # substitution
            templates.append(('v-substitution-1', 'střídat'))
            templates.append(('v-substitution-2', 'vystřídat'))

            # card
            templates.append(('v-card-1', 'dostat'))
            templates.append(('v-card-2', 'obdržet'))

        templates: List[(str, str)] = []
        init_verb_templates()
        return [t for t in templates if t[0].split('-')[1] == verb_type]

    @staticmethod
    def get_random_poss(possibilities: List[Tuple[str, str]]) -> Tuple[str, str]:
        return random.choice(possibilities)

    def transform_string_for_geneea(self):
        self.string = self.morph_params.apply_morph_params_to_string(self.string)


class Sentence:
    id: str
    constituents: List[Union[str, Template]]

    def __init__(self, msg: DP.Message):
        s = Sentence.get_sentence(msg)
        self.id = s[0]
        self.constituents = s[1]

    @staticmethod
    def get_sentence(m: DP.Message) -> (str, List[Union[str, Template]]):
        def get_sentence_result(msg: DP.Messages.Result) -> (str, List[Union[str, Template]]):
            # id type: result = 'r'
            # id subtypes: win = 'w' / draw = 'd' / loss = 'l'

            sentences: List[Tuple[str, List[Union[str, Template]]]] = []

            if msg.score.result == Types.Result.WIN:
                sentences.append(('s_r_w_1', [
                    Template(id='e-team', msg=msg, morph_params='1-.-1-.', data=msg.team_home, string=None),
                    Template(id='v-win', msg=msg, morph_params='.-0-.-1', data=None, string=None),
                    Template(id='e-team', msg=msg, morph_params='4-.-.-.', data=msg.team_away, string=None),
                    Template(id='e-score', msg=msg, morph_params='', data=msg.score, string=None)
                ]))

            elif msg.score.result == Types.Result.DRAW:
                sentences.append(('s_r_d_1', [
                    Template(id='e-team', msg=msg, morph_params='1-.-1-.', data=msg.team_home, string=None),
                    Template(id='v-draw', msg=msg, morph_params='.-0-.-1', data=None, string=None),
                    Template(id='e-team', msg=msg, morph_params='7-.-.-.', data=msg.team_away , string=None),
                    Template(id='e-score', msg=msg, morph_params='', data=msg.score, string=None),

                ]))
            else:  # msg.score.result == Types.Result.LOSS:
                sentences.append(('s_r_l_1', [
                    Template(id='e-team', msg=msg, morph_params='1-.-1-.', data=msg.team_home , string=None),
                    Template(id='v-loss', msg=msg, morph_params='.-0-.-1', data=None, string=None),
                    Template(id='e-team', msg=msg, morph_params='4-.-.-.', data=msg.team_away, string=None),
                    Template(id='e-score', msg=msg, morph_params='', data=msg.score, string=None),
                ]))

            return random.choice(sentences)

        def get_sentence_goal(msg: DP.Messages.Goal) -> (str, List[Union[str, Template]]):
            # id type: goal = 'r'
            # id subtypes: solo play = 's' / own goal = 'o' / penalty = 'p' / assistance = 'a'

            sentences: List[(str, List[Union[str, Template]])] = []
            if msg.goal_type == Types.Goal.SOLO_PLAY:
                sentences.append(('s_g_s_1', [

                    Template(id='e-time'  , msg=msg, morph_params='', data=msg.time          , string=None),
                    Template(id='v-goal'  , msg=msg, morph_params='.-0-.-.', data=None              , string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant   , string=None),
                    Template(id='w-goal'  , msg=msg, morph_params='4-.-.-.', data=None              , string=None),
                ]))

                sentences.append(('s_g_s_2', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-goal', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    Template(id='w-goal', msg=msg, morph_params='4-.-.-.', data=None, string=None),
                    "a",
                    Template(id='v-score_change', msg=msg, morph_params='', data=None, string=None),
                    "na",
                    Template(id='e-score', msg=msg, morph_params='', data=msg.current_score, string=None)
                ]))

            elif msg.goal_type == Types.Goal.ASSISTANCE:
                sentences.append(('s_g_a_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-goal', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    "po",
                    Template(id='w-assistance', msg=msg, morph_params='6-.-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='3-.-.-.', data=msg.assistance, string=None),
                    Template(id='w-goal', msg=msg, morph_params='4-.-.-.', data=None, string=None)
                ]))
            elif msg.goal_type == Types.Goal.PENALTY:
                sentences.append(('s_g_p_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-penalty', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    Template(id='w-penalty', msg=msg, morph_params='4-.-.-.', data=None, string=None)
                ]))
            elif msg.goal_type == Types.Goal.OWN_GOAL:
                sentences.append(('s_g_p_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    "si dal",
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    Template(id='w-own_goal', msg=msg, morph_params='4-.-.-.', data=None, string=None)
                ]))

            return random.choice(sentences)

        def get_sentence_substitution(msg: DP.Messages.Substitution) -> (str, List[Union[str, Template]]):
            # id type: substitution = 's'

            sentences : List[(str, List[Union[str, Template]])] = []

            sentences.append(('s_s_1', [
                Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                Template(id='v-substitution', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant_in, string=None),
                "za",
                Template(id='e-player', msg=msg, morph_params='4-.-.-.', data=msg.participant_out, string=None),
            ]))
            sentences.append(('s_s_2', [
                Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                Template(id='v-substitution', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant_in, string=None),
                Template(id='e-player', msg=msg, morph_params='4-.-.-.', data=msg.participant_out, string=None),
            ]))

            return random.choice(sentences)

        def get_sentence_card(msg: DP.Messages.Card) -> (str, List[Union[str, Template]]):
            # id type: card = 'c'
            # id subtypes: red_auto = 'a' / red_instant = 'r' / yellow = 'y'

            sentences: List[(str, List[Union[str, Template]])] = []
            if msg.card_type == Types.Card.RED_AUTO:
                sentences.append(('s_g_s_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-card', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    Template(id='w-redcard', msg=msg, morph_params='4-.-.-.', data= None, string= None)
                ]))
            elif msg.card_type == Types.Card.RED_INSTANT:
                sentences.append(('s_g_s_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-card', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    "druhou",
                    Template(id='w-yellowcard', msg=msg, morph_params='4-.-.-.', data=None, string=None),
                    "a tím pro něj zápas skončil"
                ]))
            else:  # msg.card_type == Types.Card.YELLOW:
                sentences.append(('s_g_s_1', [
                    Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                    Template(id='v-card', msg=msg, morph_params='.-0-.-.', data=None, string=None),
                    Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant, string=None),
                    Template(id='w-yellowcard', msg=msg, morph_params='4-.-.-.', data=None, string=None)
                ]))

            return random.choice(sentences)

        def get_sentence_missed_penalty(msg: DP.Messages.MissedPenalty) -> (str, List[Union[str,Template]]):
            # id type: missed penalty = 'm'
            sentences: List[(str, List[Union[str,Template]])] = []

            sentences.append(('s_m_1', [
                Template(id='e-time', msg=msg, morph_params='', data=msg.time, string=None),
                Template(id='e-player', msg=msg, morph_params='1-.-.-.', data=msg.participant_in, string=None),
                Template(id='v-failed_penalty', msg=msg, morph_params='.-0-.-.', data=msg.time, string=None),
                Template(id='w-penalty', msg=msg, morph_params='', data=msg.participant_out, string=None)
            ]))

            return random.choice(sentences)

        if type(m) is DP.Messages.Result:
            return get_sentence_result(m)
        elif type(m) is DP.Messages.Goal:
            return get_sentence_goal(m)
        elif type(m) is DP.Messages.Substitution:
            return get_sentence_substitution(m)
        elif type(m) is DP.Messages.Card:
            return get_sentence_card(m)
        elif type(m) is DP.Messages.MissedPenalty:
            return get_sentence_missed_penalty(m)
        else:
            print("Wrong types")

    def lexicalize(self):
        for tmp in self.constituents:
            if type(tmp) is Template:
                tmp.lexicalize()

    def transform_strings_for_geneea(self):
        for tmp in self.constituents:
            if type(tmp) is Template:
                tmp.transform_string_for_geneea()

    def get_string(self):
        const: List[str] = []
        for c in self.constituents:
            if type(c) is Template:
                const.append(c.string)
            else:
                const.append(c)

        # first letter is upper case
        k = 0
        while not const[0][k].isalpha() and k != len(const[0]):
            k += 1
        const[0] = const[0][:k] + const[0][k].upper() + const[0][k+1:]

        return ' '.join(const) + '.'


class Lexicalizer:

    @staticmethod
    def lexicalize(doc_plan: DP.DocumentPlan, match_data: Data.Match) -> (str, List[str]):

        random.seed(10)  # setting the seed for whole program

        title = Lexicalizer._lexicalize_message(doc_plan.title)
        body = [Lexicalizer._lexicalize_message(msg) for msg in doc_plan.body]
        return title, body

    @staticmethod
    def _lexicalize_message(msg: DP.Messages) -> str:
        sentence = Sentence(msg)
        sentence.lexicalize()
        # sentence.alternate()
        sentence.transform_strings_for_geneea()
        return sentence.get_string()
