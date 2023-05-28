from os import environ

SESSION_CONFIGS = [
    dict(
         name='social_norms_experiment',
         app_sequence=['pgg'],
         num_demo_participants=2,
    ),
]

ROOMS = [
    dict(
        name='wu_lab',
        display_name='WU Experimental Economics Lab',
        participant_label_file='participant_labels.txt',
        use_secure_urls=True
    )
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.20, participation_fee=5.00, doc=""
)

PARTICIPANT_FIELDS = ["pre_treatment_payoff","treatment","post_treatment_payoff","pay_pre_treatment"]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '3648443540366'
