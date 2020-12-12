import os
import raven

RAVEN_CONFIG = {
    #'dsn': 'https://fd1b0e57bf6e48bea9e041f33bcac319:2600077ab30b488f9e711030e3fe20ca@sentry.io/1223270',
#    'dsn': 'https://7e20336423a943d6b3cb2611c8b77480:289d61edb12c4980913c348a2a734f0f@o14549.ingest.sentry.io/267735',
    #'dsn': "https://c9036b46fecb4598a15932ce81b79075@o302288.ingest.sentry.io/5333534",
    # If you are using git, you can also automatically configure the
    # release based on the git info.
#    'release': raven.fetch_git_sha(os.path.abspath(os.pardir)),
}



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "crypto_mania",
        "USER": "monaco",
        "PASSWORD": "CNfVI{obD3qSu(A",
        "HOST": "localhost",
        "POST": "",
    }
}


DEBUG = False

ALLOWED_HOSTS = ['138.68.5.234','doxod.ru']


#BITTREX_API_KEY = '5b8611d4a0094bbb8e971afb47900df1'
#BITTREX_SECRET_KEY = b'059c048e8ce240c8ae607136857fc54d'

BITTREX_API_KEY = '575ab811d1cc4e1789aebeed80166408'
BITTREX_SECRET_KEY = '70b33e977a80472e91d8a65c8ed242e7'

BINANCE_API_KEY = 'SezlDUhf1eV84ylGwae5Vb0BUrcjWIxyL8l2GdE2EPnQ5izYdS7K1I6kq282PU1w'
BINANCE_SECRET_KEY = 'ECgXRyrsTLLMbV7ESSknpLnkihQ6kahRCKL51dukUBPsoVWPnvTKYbODTqJuZ4EP'
