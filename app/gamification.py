"""XP, levels and badges. The maths is plain functions; the database part is small and guarded."""
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Subject, QuizResult, Flashcard, StudyTask, XpEvent, UserBadge

LOCAL_OFFSET = timedelta(hours=6)  # Bangladesh time

XP_QUIZ_BASE = 10
XP_PER_CORRECT = 2
XP_PERFECT = 20
XP_CARD = 2
XP_TASK = 5
XP_DAILY = 5

ACTION_LABELS = {'quiz': 'Quiz completed', 'card': 'Flashcard learned',
                 'task': 'Study plan task done', 'daily': 'First activity of the day'}


# ---------- pure helpers ----------
def xp_for_level(n):
    """Total XP needed to reach level n (level 1 = 0, 2 = 100, 3 = 300, 4 = 600, 5 = 1000 ...)."""
    return 50 * n * (n - 1)


def level_info(xp):
    xp = max(0, int(xp))
    level = 1
    while xp >= xp_for_level(level + 1):
        level += 1
    start, nxt = xp_for_level(level), xp_for_level(level + 1)
    return {'level': level, 'xp': xp, 'into': xp - start, 'span': nxt - start,
            'percent': round((xp - start) * 100 / (nxt - start)), 'to_next': nxt - xp}


def quiz_lines(score, total):
    """Breakdown of the XP a finished quiz earns, as (label, points) pairs."""
    if total <= 0:
        return []
    lines = [('Quiz completed', XP_QUIZ_BASE), ('Correct answers', XP_PER_CORRECT * score)]
    if total >= 3 and score == total:
        lines.append(('Perfect score', XP_PERFECT))
    return [l for l in lines if l[1] > 0]


def streak_from_days(days, today):
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


BADGES = [
    {'code': 'first_quiz', 'stat': 'quizzes', 'target': 1, 'unit': 'quizzes', 'how': 'Take a quiz from any subject.', 'name': 'First steps', 'desc': 'Finish your first quiz', 'mark': '1', 'tone': 'mint',
     'check': lambda s: s['quizzes'] >= 1},
    {'code': 'quiz_10', 'stat': 'quizzes', 'target': 10, 'unit': 'quizzes', 'how': 'Keep taking quizzes, any subject counts.', 'name': 'Quiz regular', 'desc': 'Finish 10 quizzes', 'mark': '10', 'tone': 'violet',
     'check': lambda s: s['quizzes'] >= 10},
    {'code': 'perfect', 'stat': 'perfect', 'target': 1, 'unit': 'perfect quizzes', 'how': 'Answer every question right in a quiz of 3 or more questions.', 'name': 'Flawless', 'desc': 'Score 100% on a quiz of 3+ questions', 'mark': '100', 'tone': 'amber',
     'check': lambda s: s['perfect'] >= 1},
    {'code': 'streak_3', 'stat': 'streak', 'target': 3, 'unit': 'days', 'how': 'Do any study activity (quiz, flashcard, task) on 3 days in a row.', 'name': 'On a roll', 'desc': 'Study 3 days in a row', 'mark': '3d', 'tone': 'coral',
     'check': lambda s: s['streak'] >= 3},
    {'code': 'streak_7', 'stat': 'streak', 'target': 7, 'unit': 'days', 'how': 'Do any study activity on 7 days in a row.', 'name': 'Week warrior', 'desc': 'Study 7 days in a row', 'mark': '7d', 'tone': 'coral',
     'check': lambda s: s['streak'] >= 7},
    {'code': 'cards_25', 'stat': 'cards_known', 'target': 25, 'unit': 'cards', 'how': 'Mark flashcards as known in the Flashcards page.', 'name': 'Card collector', 'desc': 'Learn 25 flashcards', 'mark': '25', 'tone': 'mint',
     'check': lambda s: s['cards_known'] >= 25},
    {'code': 'tasks_10', 'stat': 'tasks_done', 'target': 10, 'unit': 'tasks', 'how': 'Tick tasks in your Study Plan.', 'name': 'Plan keeper', 'desc': 'Complete 10 study plan tasks', 'mark': '10', 'tone': 'amber',
     'check': lambda s: s['tasks_done'] >= 10},
    {'code': 'level_5', 'stat': 'level', 'target': 5, 'unit': 'level', 'how': 'Earn 1000 XP in total.', 'name': 'Rising star', 'desc': 'Reach level 5', 'mark': 'L5', 'tone': 'violet',
     'check': lambda s: s['level'] >= 5},
]
BADGE_BY_CODE = {b['code']: b for b in BADGES}


def badge_public(b):
    return {k: b[k] for k in ('code', 'name', 'desc', 'mark', 'tone', 'target', 'unit', 'how')}


# ---------- database part ----------
def local_today():
    return (datetime.utcnow() + LOCAL_OFFSET).date()


def total_xp(user_id):
    return sum(e.points for e in XpEvent.query.filter_by(user_id=user_id).all())


def user_results(user_id):
    results = []
    for s in Subject.query.filter_by(user_id=user_id).all():
        results += QuizResult.query.filter_by(subject_id=s.id).all()
    return results


def activity_days(user_id, results=None):
    """Every local date on which the student did something (took a quiz or earned XP)."""
    if results is None:
        results = user_results(user_id)
    days = {(r.date_taken + LOCAL_OFFSET).date() for r in results if r.date_taken}
    for e in XpEvent.query.filter_by(user_id=user_id).all():
        if e.created_at:
            days.add((e.created_at + LOCAL_OFFSET).date())
    return days


def gather_stats(user_id, total, today):
    results = user_results(user_id)
    return {
        'quizzes': len(results),
        'perfect': sum(1 for r in results if r.total_questions >= 3 and r.score == r.total_questions),
        'cards_known': Flashcard.query.filter_by(user_id=user_id, known=True).count(),
        'tasks_done': StudyTask.query.filter_by(user_id=user_id, done=True).count(),
        'streak': streak_from_days(activity_days(user_id, results), today),
        'level': level_info(total)['level'],
    }


def grant_badges(user_id, total, today):
    have = {b.code for b in UserBadge.query.filter_by(user_id=user_id).all()}
    stats = gather_stats(user_id, total, today)
    new = []
    for b in BADGES:
        if b['code'] not in have and b['check'](stats):
            db.session.add(UserBadge(user_id=user_id, code=b['code']))
            new.append(b)
    return new


def _award(user_id, action, lines, ref_key, subject_id=None):
    lines = [(label, pts) for label, pts in lines if pts > 0]
    if not lines or XpEvent.query.filter_by(user_id=user_id, ref_key=ref_key).first():
        return None

    today = local_today()
    before_total = total_xp(user_id)
    gained = sum(p for _, p in lines)
    db.session.add(XpEvent(user_id=user_id, subject_id=subject_id, action=action, points=gained, ref_key=ref_key))

    day_key = f'daily:{today.isoformat()}'
    if not XpEvent.query.filter_by(user_id=user_id, ref_key=day_key).first():
        db.session.add(XpEvent(user_id=user_id, action='daily', points=XP_DAILY, ref_key=day_key))
        lines.append(('First activity today', XP_DAILY))
        gained += XP_DAILY

    try:
        db.session.flush()
    except IntegrityError:  # the same award arrived twice at once
        db.session.rollback()
        return None

    after_total = before_total + gained
    new_badges = grant_badges(user_id, after_total, today)
    db.session.commit()

    before, after = level_info(before_total), level_info(after_total)
    return {'gained': gained,
            'lines': [{'label': label, 'points': pts} for label, pts in lines],
            'level': after, 'leveled_up': after['level'] > before['level'],
            'badges': [badge_public(b) for b in new_badges]}


def award(user_id, action, lines, ref_key, subject_id=None):
    """Gives XP once per ref_key. Never raises: a problem here must not break quizzes or cards."""
    try:
        return _award(user_id, action, lines, ref_key, subject_id)
    except Exception as e:
        print('XP ERROR:', repr(e))
        try:
            db.session.rollback()
        except Exception:
            pass
        return None


def backfill(user_id):
    """First visit after this feature arrives: turn past quizzes, known cards and done tasks into XP."""
    if XpEvent.query.filter_by(user_id=user_id).first():
        return
    added = False
    for s in Subject.query.filter_by(user_id=user_id).all():
        for r in QuizResult.query.filter_by(subject_id=s.id).all():
            pts = sum(p for _, p in quiz_lines(r.score, r.total_questions))
            if pts:
                db.session.add(XpEvent(user_id=user_id, subject_id=s.id, action='quiz', points=pts,
                                       ref_key=f'quiz:{r.id}', created_at=r.date_taken))
                added = True
    for c in Flashcard.query.filter_by(user_id=user_id, known=True).all():
        db.session.add(XpEvent(user_id=user_id, subject_id=c.subject_id, action='card', points=XP_CARD,
                               ref_key=f'card:{c.id}'))
        added = True
    for t in StudyTask.query.filter_by(user_id=user_id, done=True).all():
        db.session.add(XpEvent(user_id=user_id, subject_id=t.subject_id, action='task', points=XP_TASK,
                               ref_key=f'task:{t.id}'))
        added = True
    if added:
        db.session.flush()
        grant_badges(user_id, total_xp(user_id), local_today())
        db.session.commit()


def _earned(user_id):
    return {b.code: b for b in UserBadge.query.filter_by(user_id=user_id).all()}


def dashboard_summary(user_id):
    """Small summary for the dashboard card, or None if anything goes wrong."""
    try:
        backfill(user_id)
        earned = _earned(user_id)
        recent = sorted(earned.values(), key=lambda b: b.earned_at or datetime.min, reverse=True)[:4]
        return {'level': level_info(total_xp(user_id)),
                'recent': [badge_public(BADGE_BY_CODE[b.code]) for b in recent if b.code in BADGE_BY_CODE],
                'earned': sum(1 for c in earned if c in BADGE_BY_CODE), 'total': len(BADGES)}
    except Exception as e:
        print('XP SUMMARY ERROR:', repr(e))
        try:
            db.session.rollback()
        except Exception:
            pass
        return None


def achievements_data(user_id):
    backfill(user_id)
    earned = _earned(user_id)
    total = total_xp(user_id)
    stats = gather_stats(user_id, total, local_today())
    badges = []
    for b in BADGES:
        row = earned.get(b['code'])
        item = badge_public(b)
        item['current'] = min(stats[b['stat']], b['target'])
        item['percent'] = int(100 * item['current'] / b['target'])
        item['earned'] = row is not None
        item['date'] = (row.earned_at + LOCAL_OFFSET).strftime('%d %b %Y') if row and row.earned_at else ''
        badges.append(item)
    events = sorted(XpEvent.query.filter_by(user_id=user_id).all(), key=lambda e: e.id, reverse=True)[:15]
    recent = [{'label': ACTION_LABELS.get(e.action, e.action), 'points': e.points,
               'when': (e.created_at + LOCAL_OFFSET).strftime('%d %b, %I:%M %p') if e.created_at else ''}
              for e in events]
    return {'level': level_info(total_xp(user_id)), 'badges': badges,
            'earned_count': sum(1 for b in badges if b['earned']), 'recent': recent}
