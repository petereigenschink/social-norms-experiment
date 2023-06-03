from otree.api import *
import itertools
import random

class C(BaseConstants):
    NAME_IN_URL = 'pggsn'

    PLAYERS_PER_GROUP = 2 # TODO: Change to 4
    NUM_ROUNDS = 2 # TODO: Change to 20
    PRE_TREATMENT_ROUNDS=NUM_ROUNDS/2
    TREATMENTS={
        "SN": "SN",
        "SNP": "SNP",
        "DN": "DN",
        "DNP": "DNP"
    }
    ENDOWMENT = 20
    EFFICIENCY_FACTOR = 2
    PAY_PRE_TREATMENT=random.choice([True, False])
    PAYOFF_CONVERSION_RATE=0.07
    NUM_SEATS=32
    SURVEY_CHOICES=[1,2,3,4,5]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    treatment = models.StringField()
    total_contribution = models.IntegerField()
    total_pool = models.IntegerField()
    individual_share = models.IntegerField()

class Player(BasePlayer):
    final_real_payoff = models.FloatField()
    seat_number = models.IntegerField(
        min=1, max=C.NUM_SEATS, label=f'What is your seat number (1-{C.NUM_SEATS})?'
    )
    contribution = models.IntegerField(
        min=0, max=C.ENDOWMENT, label=f'How much do you contribute (0-{C.ENDOWMENT} tokens)?'
    )
    
    survey_q1=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... like I was working together with my group partners towards a common goal.'
    )
    survey_q2=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... I was working for my own good instead of the common good.'
    )
    survey_q3=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... pressured into contributing to the public account.'
    )
    survey_q4=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... obligated to contribute to the public account.'
    )
    survey_q5=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... it was possible to contribute more to the public account, compared to the first half.'
    )
    survey_q6=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... the contributions would not change, compared to the first half.'
    )
    survey_q7=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... trusted in my group partners to contribute to the public account.'
    )
    survey_q8=models.IntegerField(
        choices=C.SURVEY_CHOICES,
        widget=widgets.RadioSelectHorizontal,
        label='... felt that if I did my part in contributing to the public account, the others would do the same.'
    )

# FUNCTIONS
def set_pgg_round_payoffs(group: Group):
    players = group.get_players()
    contributions = [p.contribution for p in players]
    group.total_contribution = sum(contributions)
    group.total_pool = group.total_contribution * C.EFFICIENCY_FACTOR
    group.individual_share = round(
        group.total_pool / C.PLAYERS_PER_GROUP
    )
    for p in players:
        p.payoff = C.ENDOWMENT - p.contribution + group.individual_share

# TODO: Implement logic for imbalanced groups in first session
def assign_treatments(subsession: Subsession):
    subsession.group_randomly()

    treatments = itertools.cycle(C.TREATMENTS.values())
    for group in subsession.get_groups():
        group.treatment = next(treatments)
        for player in group.get_players():
            player.participant.vars["treatment"] = group.treatment

def determine_final_payoff(player, timeout_happened):
    if player.round_number != C.NUM_ROUNDS:
        return

    player.participant.vars["post_treatment_payoff"]=player.participant.payoff

    payoff=player.participant.payoff
    if C.PAY_PRE_TREATMENT:
        payoff=player.participant.vars["pre_treatment_payoff"]
    
    final_real_payoff=to_real_currency(payoff)
    player.participant.payoff=final_real_payoff
    player.participant.vars["real_payoff"]=final_real_payoff
    player.final_real_payoff=final_real_payoff

def to_real_currency(num):
    return round(C.PAYOFF_CONVERSION_RATE*int(num),2)

# PAGES
class SeatNumber(Page):
    form_model = 'player'
    form_fields = ['seat_number']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.label=str(player.seat_number)

class TreatmentAssignment(WaitPage):

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.PRE_TREATMENT_ROUNDS + 1

    after_all_players_arrive = assign_treatments

class TreatmentInfo(Page):

    timeout_seconds=30

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.PRE_TREATMENT_ROUNDS + 1

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.vars["pre_treatment_payoff"]=player.participant.payoff
        player.participant.payoff = 0

class Contribute(Page):
    form_model = 'player'
    form_fields = ['contribution']

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_pgg_round_payoffs

class Results(Page):

    timeout_seconds=15

    @staticmethod
    def vars_for_template(player):
        return {
            "payoff": int(player.payoff)
        }
    
    before_next_page=determine_final_payoff

class Survey(Page):
    form_model = 'player'
    form_fields = [f'survey_q{i}' for i in range(1,9)]

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

class OverallResults(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        pre_treatment_payoff = int(player.participant.vars["pre_treatment_payoff"])
        post_treatment_payoff = int(player.participant.vars["post_treatment_payoff"])
        return {
            "pre_treatment_payoff": pre_treatment_payoff,
            "real_pre_treatment_payoff": to_real_currency(pre_treatment_payoff),
            "post_treatment_payoff": post_treatment_payoff,
            "real_post_treatment_payoff": to_real_currency(post_treatment_payoff),
            "payoff": player.participant.payoff
        }

class ThankYou(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

page_sequence = [SeatNumber, TreatmentAssignment, TreatmentInfo, Contribute,
                    ResultsWaitPage, Results, Survey, OverallResults, ThankYou]

# Payoff export in data tab
def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'participant_label', 'payoff_real']
    participants={}
    for p in players:
        participant = p.participant
        participants[participant.code]=participant
    for participant in participants.values():
        yield [participant.session.code, participant.code, participant.label, str(participant.vars["real_payoff"] if "real_payoff" in participant.vars else 0.0)]

"""
# Data export
def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'participant_label', 'treatment', 'round_number', 'group_id_in_subsession', 'player_id_in_group', 'contribution', 'payoff']
    participants={}
    for p in players:

        treatment=None
        try:
            treatment=p.participant.treatment
        except KeyError:
            treatment=''

        yield [
            p.session.code,
            p.participant.code,
            p.participant.label,
            treatment,
            p.round_number,
            p.group.id_in_subsession,
            p.id_in_group,
            p.contribution,
            p.payoff
        ]
"""