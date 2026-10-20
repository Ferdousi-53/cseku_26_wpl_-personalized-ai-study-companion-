"""Builds everything the dashboard page needs: stats, streak, trend, weak topics."""
from datetime import datetime, timedelta

from app.models import Subject, Document, QuizResult, TopicPerformance, StudyTask
from app.gamification import activity_days, dashboard_summary

LOCAL_OFFSET = timedelta(hours=6)  # Bangladesh time
TONES = ['coral', 'mint', 'amber', 'violet']  # one accent colour per subject card


def _pct(result):
    return result.score * 100 / result.total_questions if result.total_questions else 0


def _greeting(hour):
    if hour < 12:
        return 'Good morning'
    if hour < 18:
        return 'Good afternoon'
    return 'Good evening'


def _streak(days, today):
    """`days` is the set of dates the student studied on (quizzes and anything that earned XP)."""
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        week.append({'on': d in days, 'label': d.strftime('%a %d %b')})
    return streak, week


def _trend(results):
    last = sorted(results, key=lambda r: r.date_taken)[-10:]
    if len(last) < 2:
        return None
    left, right, top, bottom, base = 20, 623, 20, 160, 170
    step = (right - left) / (len(last) - 1)
    pts = [(round(left + i * step, 1), round(bottom - _pct(r) / 100 * (bottom - top), 1))
           for i, r in enumerate(last)]
    line = ' '.join(f'{x},{y}' for x, y in pts)
    area = 'M' + ' L'.join(f'{x},{y}' for x, y in pts) + f' L{pts[-1][0]},{base} L{pts[0][0]},{base}Z'
    return {'line': line, 'area': area, 'last': pts[-1], 'count': len(last)}


def build_dashboard(user):
    now = datetime.utcnow() + LOCAL_OFFSET
    today = now.date()

    subjects = Subject.query.filter_by(user_id=user.id).all()
    ids = [s.id for s in subjects]
    results = QuizResult.query.filter(QuizResult.subject_id.in_(ids)).all() if ids else []
    topics = TopicPerformance.query.filter(TopicPerformance.subject_id.in_(ids)).all() if ids else []
    doc_count = Document.query.filter(Document.subject_id.in_(ids)).count() if ids else 0

    # weak topics (accuracy under 70%), grouped by subject
    weak_by_subject = {}
    weak_all = []
    names = {s.id: s.subject_name for s in subjects}
    for t in topics:
        total = (t.correct_count or 0) + (t.wrong_count or 0)
        if total == 0:
            continue
        acc = round((t.correct_count or 0) * 100 / total)
        if acc < 70:
            row = {'topic': t.topic, 'accuracy': acc, 'subject_id': t.subject_id,
                   'subject_name': names.get(t.subject_id, '')}
            weak_all.append(row)
            if t.subject_id not in weak_by_subject or acc < weak_by_subject[t.subject_id]['accuracy']:
                weak_by_subject[t.subject_id] = row
    weak_all.sort(key=lambda r: r['accuracy'])

    subjects_data = []
    for i, s in enumerate(subjects):
        days_left, urgency = None, ''
        if s.exam_date:
            days_left = (s.exam_date - today).days
            if 0 <= days_left <= 7:
                urgency = 'urgent'
            elif 7 < days_left <= 30:
                urgency = 'soon'
        s_results = [r for r in results if r.subject_id == s.id]
        avg = round(sum(_pct(r) for r in s_results) / len(s_results)) if s_results else None
        weak = weak_by_subject.get(s.id)
        subjects_data.append({
            'subject': s, 'id': s.id, 'name': s.subject_name,
            'tone': TONES[i % len(TONES)], 'days_left': days_left, 'urgency': urgency,
            'avg': avg, 'weak_topic': weak['topic'] if weak else None,
            'weak_acc': weak['accuracy'] if weak else None,
        })

    upcoming = sorted((d for d in subjects_data if d['days_left'] is not None and d['days_left'] >= 0),
                      key=lambda d: d['days_left'])
    focus = upcoming[0] if upcoming else (subjects_data[0] if subjects_data else None)

    plan_today = None
    if focus:
        todays = (StudyTask.query.filter_by(user_id=user.id, subject_id=focus['id'], task_date=today)
                  .order_by(StudyTask.position, StudyTask.id).all())
        if todays:
            next_task = next((t for t in todays if not t.done), None)
            plan_today = {'total': len(todays), 'done': sum(1 for t in todays if t.done),
                          'next_title': next_task.title if next_task else None}

    week_start = today - timedelta(days=6)
    quizzes_this_week = sum(1 for r in results if (r.date_taken + LOCAL_OFFSET).date() >= week_start)
    avg_score = round(sum(_pct(r) for r in results) / len(results)) if results else None
    streak, week = _streak(activity_days(user.id, results), today)

    return {
        'greeting': _greeting(now.hour),
        'today_label': now.strftime('%A, %d %B'),
        'subjects_data': subjects_data,
        'upcoming': upcoming[:4],
        'focus': focus,
        'plan_today': plan_today,
        'gam': dashboard_summary(user.id),
        'weak_list': weak_all[:4],
        'streak': streak,
        'week': week,
        'trend': _trend(results),
        'stats': {
            'subjects': len(subjects),
            'exams_soon': sum(1 for d in upcoming if d['days_left'] <= 30),
            'quizzes': len(results),
            'quizzes_week': quizzes_this_week,
            'avg_score': avg_score,
            'documents': doc_count,
        },
    }
