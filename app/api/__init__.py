from .auth import auth_bp
from .user import user_bp
from .family import family_bp
from .dictation import dictation_bp

__all__ = [
    'auth_bp',
    'user_bp',
    'family_bp',
    'dictation_bp'
]
