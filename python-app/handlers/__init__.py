from .start import register_start_handlers
from .registration import register_registration_handlers
from .advanced import register_advanced_handlers


def register_handlers(dp):
    register_start_handlers(dp)
    register_registration_handlers(dp)
    register_advanced_handlers(dp)
