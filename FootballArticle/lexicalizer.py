"""Lexicalize document plan with specific language expressions and
also transforming lexicalized text into valid input for Geneea.
Input is document plan and match data, output is string that can be an input of Geneea API.
"""

# Python's libraries
import random
from typing import List, Tuple, Union
# Other parts of the code
import Types
import document_planner as di
import Data


class MorphParams:
    """Class to transform linguistic requirements into Geneea well-build input. """
    case: Types.Morph.Case
    tense: Types.Morph.Tense
    ref: None
    agr: None

    def __init__(self, string_id: str):
        params: (Types.Morph.Case, Types.Morph.Tense, str, str) = MorphParams.get_morph_params(string_id)
        self.case = params[0]
        self.tense = params[1]
        self.ref = params[2]
        self.agr = params[3]

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

    def apply_morph_params_to_string(self, constituent: str) -> str:
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


class Template:
    id: str
    morph_params: MorphParams
    explicit_data: Types.ExplicitEntityData
    string: str

    def __init__(self, id_: str, morph_params: str, explicit_data: Types.ExplicitEntityData):
        self.id = id_
        self.morph_params = MorphParams(morph_params)
        self.explicit_data = explicit_data
        self.string = ''

    def lexicalize(self):
        constituent_type = self.id.split('-')[0]
        possibilities: List[Tuple[str, str]] = []

        if constituent_type == 'e':   # ENTITY
            possibilities = Template.get_string_poss_entity(self)
        elif constituent_type == 'w':   # WORD
            word_type = self.id.split('-')[1]
            possibilities = Template.get_string_poss_word(word_type)
        elif constituent_type == 'v':   # VERB
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
            templates.append(('w-assistance-3', 'přihrávka'))

            # penalty
            templates.append(('w-penalty-1', 'penalta'))
            templates.append(('w-penalty-2', 'pokutový kop'))
            templates.append(('w-penalty-3', 'jedenáctka'))

            # own goal
            templates.append(('w-own_goal-1', 'vlastňák'))
            templates.append(('w-own_goal-2', 'vlastní gól'))
            templates.append(('w-own_goal-3', 'vlastenec'))

            # yellow card
            templates.append(('w-yellow_card-1', 'žlutá'))
            templates.append(('w-yellow_card-2', 'žlutá karta'))

            # red card
            templates.append(('w-red_card-1', 'červená'))
            templates.append(('w-red_card-2', 'červená karta'))

            # draw
            templates.append(('w-draw-1', 'remíza'))
            templates.append(('w-draw-2', 'plichta'))
            templates.append(('w-draw-3', 'nerozhodný výsledek'))

            # lose
            templates.append(('w-lose-1', 'porážka'))
            templates.append(('w-lose-2', 'prohra'))
            templates.append(('w-lose-3', 'debakl'))
            templates.append(('w-lose-4', 'ostuda'))

            # win
            templates.append(('w-win-1', 'vítězství'))
            templates.append(('w-win-2', 'výhra'))
            templates.append(('w-win-3', 'zdar'))

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
            templates.append(('v-score_change-3', 'zvýšil'))

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
            templates.append(('v-card-2', 'vyfasovat'))

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
    simple: bool
    constituents: List[Union[str, Template]]
    frequency: int

    def __init__(self, id: str, simple: bool, constituents: List[Union[str, Template]]):
        self.id = id
        self.simple = simple
        self.constituents = constituents
        self.frequency = 0

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

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
        const[0] = const[0][:k] + const[0][k].upper() + const[0][k + 1:]


class SentenceHandler:
    sentences: List[Sentence]
    used_sentences: List[Sentence]

    def __init__(self):
        self.sentences = []

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
        while index + 1 < len(self.sentences) and self.sentences[index] == self.sentences[index+1]:
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
        print('---------------------------------')
        random.shuffle(self.sentences)
        self.sentences.sort()
        self.put_simple_first()
        self.print_sentences_count()
        print('---------------------------------')

    def init_sentences(self):
        def init_sentence_result():
            type_ = 'r'
            # id subtypes: win = 'w' / draw = 'd' / loss = 'l'

            # win
            subtype = 'w'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Template(id_='v-win', morph_params='.-0-.-1', explicit_data=None),
                Template(id_='e-team', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Template(id_='e-score', morph_params='', explicit_data=None)]))

            # draw
            subtype = 'd'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Template(id_='v-draw', morph_params='.-0-.-1', explicit_data=None),
                Template(id_='e-team', morph_params='7-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Template(id_='e-score', morph_params='', explicit_data=None)]))

            # lose
            subtype = 'l'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-team', morph_params='1-.-1-.', explicit_data=Types.ExplicitEntityData.TEAM_HOME),
                Template(id_='v-loss', morph_params='.-0-.-1', explicit_data=None),
                Template(id_='e-team', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.TEAM_AWAY),
                Template(id_='e-score', morph_params='', explicit_data=None)]))

        def init_sentence_goal():
            type_ = 'g'
            # id subtypes: solo play = 's' / own goal = 'o' / penalty = 'p' / assistance = 'a'

            # Types.Goal.SOLO_PLAY
            subtype = 's'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                Template(id_='w-goal', morph_params='4-.-.-.', explicit_data=None)]))

            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), False, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                Template(id_='w-goal', morph_params='4-.-.-.', explicit_data=None),
                "a",
                Template(id_='v-score_change', morph_params='', explicit_data=None),
                "na",
                Template(id_='e-score', morph_params='', explicit_data=Types.ExplicitEntityData.CURRENT_SCORE)]))

            # Types.Goal.ASSISTANCE
            subtype = 'a'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-goal', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                "po",
                Template(id_='w-assistance', morph_params='6-.-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='3-.-.-.', explicit_data=Types.ExplicitEntityData.ASSISTANCE),
                Template(id_='w-goal', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Goal.PENALTY
            subtype = 'p'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-penalty', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                Template(id_='w-penalty', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Goal.OWN_GOAL
            subtype = 'o'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                "si dal",
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                Template(id_='w-own_goal', morph_params='4-.-.-.', explicit_data=None)]))

        def init_sentence_substitution():
            type_ = 's'
            subtype = ''

            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-substitution',morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                "za",
                Template(id_='e-player', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-substitution', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_IN),
                Template(id_='e-player', morph_params='4-.-.-.', explicit_data=Types.ExplicitEntityData.PARTICIPANT_OUT)]))

        def init_sentence_card():
            type_ = 'c'
            # id subtypes: red_auto = 'a' / red_instant = 'r' / yellow = 'y'

            # Types.Card.RED_AUTO
            subtype = 'a'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                    Template(id_='e-time', morph_params='', explicit_data=None),
                    Template(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                    Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                    Template(id_='w-redcard', morph_params='4-.-.-.', explicit_data=None)]))

            # Types.Card.RED_INSTANT
            subtype = 'r'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                "po druhé žluté kartě červenou"]))

            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), False, [
                    Template(id_='e-time', morph_params='', explicit_data=None),
                    Template(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                    Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                    "druhou",
                    Template(id_='w-yellowcard', morph_params='4-.-.-.', explicit_data=None),
                    "a tím pro něj zápas skončil"]))


            # Types.Card.YELLOW
            subtype = 'y'
            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                    Template(id_='e-time', morph_params='', explicit_data=None),
                    Template(id_='v-card', morph_params='.-0-.-.', explicit_data=None),
                    Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                    Template(id_='w-yellowcard', morph_params='4-.-.-.', explicit_data=None)]))

        def init_sentence_missed_penalty():
            type_ = 'm'
            subtype = ''

            self.sentences.append(Sentence(_init_sentence_key(type_, subtype), True, [
                Template(id_='e-time', morph_params='', explicit_data=None),
                Template(id_='e-player', morph_params='1-.-.-.', explicit_data=None),
                Template(id_='v-failed_penalty', morph_params='.-0-.-.', explicit_data=None),
                Template(id_='w-penalty', morph_params='', explicit_data=None)]))

        def _init_sentence_key(type_: str, subtype: str) -> str:
            d = '_'
            if subtype != '':
                subtype = d + subtype
            return 's' + d + type_ + subtype

        init_sentence_result()
        init_sentence_goal()
        init_sentence_substitution()
        init_sentence_card()
        init_sentence_missed_penalty()
        self.sentences.sort()
        self.init_sentences_count()
        self.used_sentences = []
        self.print_sentences_count()

    def print_sentences_count(self):
        for s in self.sentences:
            diff = 'simple'
            if not s.simple:
                diff = 'difficult'
            print("(id = "+s.id+", " + diff + ", count = " + str(s.frequency) + ")")

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

    def get_sentence(self, m: di.Message) -> Sentence:
        print('***************************************************************************')
        print('Message to get sentence for: ' + str(m))

        key = self._get_sentence_key(m)
        print('key: ' + key)
        (found, sentence_index) = self.try_find_sentence(key)
        print('Found: ' + str(found), ', sentence_index:' + str(sentence_index))
        if found:
            sentence = self.sentences.pop(sentence_index)
            self.used_sentences.append(sentence)
            #self.print_sentences_count()
            return sentence
        else:
            return self.get_random_used(key)

    def create_sentences_templates(self, doc_plan: di.DocumentPlan) -> (Sentence, List[Sentence]):
        self.randomize_sentences_order()

        title_sentence = self.get_sentence(doc_plan.title)
        body_sentences = [self.get_sentence(msg) for msg in doc_plan.body]

        for s in body_sentences:
            diff = 'simple'
            if not s.simple:
                diff = 'difficult'
            print("(id = "+s.id+", " + diff + ", count = " + str(s.frequency) + ")")

        return title_sentence, body_sentences

    def _init_sentence_key(self, m: di.Message) -> str:
        d = '_'
        s = 's' + d

        subtype = ''
        if type(m) is di.Messages.Result:
            type_ = 'r'
            if m.score.result == Types.Result.WIN:
                subtype = 'w'
            elif m.score.result == Types.Result.DRAW:
                subtype = 'd'
            else:   # Types.Result.DRAW
                subtype = 'l'
        elif type(m) is di.Messages.Goal:
            type_ = 'g'
            if m.goal_type == Types.Goal.SOLO_PLAY:
                subtype = 's'
            elif m.goal_type == Types.Goal.ASSISTANCE:
                subtype = 'a'
            elif m.goal_type == Types.Goal.OWN_GOAL:
                subtype = 'o'
            else:   # Types.Goal.PENALTY
                subtype = 'p'
        elif type(m) is di.Messages.Substitution:
            type_ = 's'
        elif type(m) is di.Messages.Card:
            type_ = 'c'
            if m.card_type == Types.Card.RED_AUTO:
                subtype = 'a'
            elif m.card_type == Types.Card.RED_INSTANT:
                subtype = 'r'
            else:   # Types.Card.YELLOW
                subtype = 'y'
        else:  # type(m) is di.Messages.MissedPenalty:
            type_ = 'm'

        if subtype == '':
            s += type_
        else:
            s += type_ + d + subtype

        return s


class Lexicalizer:

    @staticmethod
    def lexicalize_articles(doc_plan: di.DocumentPlan, match_data: Data.Match,  text_count: int) -> (str, List[str]):
        sh: SentenceHandler = SentenceHandler()
        sh.init_sentences()
        (title_sentence, body_sentences) = sh.create_sentences_templates(doc_plan)
        title = Lexicalizer._lexicalize_message(title_sentence)
        body = [Lexicalizer._lexicalize_message(sentence) for sentence in body_sentences]

        #return title, body
        return '', None

    #def _get_sentences() -> dict:

    @staticmethod
    def _lexicalize_message(sentence: Sentence) -> str:
        sentence.lexicalize()
        # sentence.alternate()
        sentence.transform_strings_for_geneea()
        return sentence.get_string()
