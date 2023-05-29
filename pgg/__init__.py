from otree.api import *
import itertools
import random

class C(BaseConstants):
    NAME_IN_URL = 'pgg'

    PLAYERS_PER_GROUP = 2 # 4
    NUM_ROUNDS = 2 # 20
    PRE_TREATMENT_ROUNDS=NUM_ROUNDS/2
    TREATMENTS={
        "SN": "SN",
        "SNP": "SNP",
        "DN": "DN",
        "DNP": "DNP"
    }
    ENDOWMENT = cu(20)
    EFFICIENCY_FACTOR = 2


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()

class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0, max=C.ENDOWMENT, label=f'How much do you contribute (0-{C.ENDOWMENT})?'
    )

# FUNCTIONS
def set_pgg_round_payoffs(group: Group):
    players = group.get_players()
    contributions = [p.contribution for p in players]
    group.total_contribution = sum(contributions)
    group.individual_share = (
        group.total_contribution * C.EFFICIENCY_FACTOR / C.PLAYERS_PER_GROUP
    )
    for p in players:
        p.payoff = C.ENDOWMENT - p.contribution + group.individual_share

def assign_treatments(subsession: Subsession):
    subsession.group_randomly()

    treatments = itertools.cycle(C.TREATMENTS.values())
    for group in subsession.get_groups():
        treatment = next(treatments)
        for player in group.get_players():
            player.participant.treatment = treatment

def determine_final_payoff(player, timeout_happened):
    if player.round_number != C.NUM_ROUNDS:
        return

    player.participant.post_treatment_payoff=player.participant.payoff

    player.participant.pay_pre_treatment=random.choice([True, False])
    if player.participant.pay_pre_treatment:
        player.participant.payoff=player.participant.pre_treatment_payoff

# PAGES
class TreatmentAssignment(WaitPage):

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.PRE_TREATMENT_ROUNDS + 1

    after_all_players_arrive = assign_treatments

class TreatmentInfo(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.PRE_TREATMENT_ROUNDS + 1

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.pre_treatment_payoff=player.participant.payoff
        player.participant.payoff = 0

class Contribute(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player):
        
        treated=None
        try:
            player.participant.treatment
            treated=True
        except KeyError:
            treated=False

        return {
            "treated": treated
        }

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_pgg_round_payoffs

class Results(Page):
    before_next_page=determine_final_payoff

class OverallResults(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        return {
            "participation_fee": player.session.config['participation_fee'],
            "real_pre_treatment_payoff": player.participant.pre_treatment_payoff.to_real_world_currency(player.session),
            "real_post_treatment_payoff": player.participant.post_treatment_payoff.to_real_world_currency(player.session),
            "total_payoff": player.participant.post_treatment_payoff.to_real_world_currency(player.session)
        }

page_sequence = [TreatmentAssignment, TreatmentInfo, Contribute, ResultsWaitPage, Results, OverallResults]

# Payoff export
def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'participant_label', 'payoff']
    participants={}
    for p in players:
        participant = p.participant
        participants[participant.code]=participant
    for participant in participants.values():
        yield [participant.session.code, participant.code, participant.label, participant.payoff]