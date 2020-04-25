from logging.config import dictConfig


def init_logging(loglevel='info'):
    dictConfig({

        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(name)s [%(filename)s][%(levelname)s][%(lineno)d] : %(message)s'
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
