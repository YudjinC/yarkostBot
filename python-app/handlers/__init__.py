from .start import register_start_handlers
from .registration import register_registration_handlers
from .advanced import register_advanced_handlers
from .administrator import register_administrator_handlers
from .fallback import register_fallback_handlers


def register_handlers(dp):
    register_start_handlers(dp)
    register_registration_handlers(dp)
    register_advanced_handlers(dp)
    register_administrator_handlers(dp)
    register_fallback_handlers(dp)
