"""Premium settings and helpers. Change the values below to suit you."""
import re
from datetime import datetime, timedelta
from functools import wraps

from flask import flash, redirect, url_for, current_app
from flask_login import current_user

# ---- settings you can edit ----
BKASH_NUMBER = '01883496546'
PRICE_BDT = 99                # price of one premium period
PREMIUM_DAYS = 30             # how long one payment lasts
ADMIN_EMAILS = ['wplwork230@gmail.com']   # accounts that can approve payments (use the email you log in with)

FEATURES = {
    'summary': 'Smart Summary',
    'exam': 'Mock Exam',
}

TRX_RE = re.compile(r'^[A-Z0-9]{8,14}$')


def clean_trx(value):
    return re.sub(r'\s+', '', (value or '')).upper()


def clean_phone(value):
    digits = re.sub(r'[\s\-+]', '', value or '')
    if digits.startswith('88') and len(digits) == 13:
        digits = digits[2:]
    return digits


def valid_phone(value):
    return bool(re.fullmatch(r'01[3-9]\d{8}', value or ''))


def extend_premium(user):
    """Adds one premium period; time left on an active plan is kept."""
    start = max(datetime.utcnow(), user.premium_until or datetime.utcnow())
    user.premium_until = start + timedelta(days=PREMIUM_DAYS)


def days_left(user):
    if not user.premium_until:
        return 0
    return max(0, (user.premium_until - datetime.utcnow()).days + 1)


def premium_required(feature):
    """Put under @login_required. Free users are sent to the Upgrade page."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.has_premium:
                flash(f'{FEATURES.get(feature, "Ei feature")} ekta Premium feature. Upgrade korle use korte parbe.')
                return redirect(url_for('upgrade', feature=feature))
            return fn(*args, **kwargs)
        return wrapper
    return decorator
