from logging.config import dictConfig


def init_logging(loglevel='info'):
    dictConfig({

        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(name)s [%(levelname)s]: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': loglevel.upper(),
                'class': 'logging.FileHandler',
                'formatter': 'default',
                'filename': 'log.txt',
                'mode': 'w',

            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': loglevel.upper(),
                'propagate': True
            },
        }
    })
