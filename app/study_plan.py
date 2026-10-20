"""Builds a day-by-day study plan with the AI, using the student's quiz results and notes."""
import json
import random
from datetime import timedelta

from app.gemini import generate_text, GeminiError
from app.models import TopicPerformance
from app.rag import collection

MAX_DAYS = 14
KINDS = {'read', 'revise', 'practice', 'quiz'}
TASKS_PER_DAY = {1: 2, 2: 3, 3: 5}


def plan_window(exam_date, today):
    """Dates from today up to the exam day (or 14 days, whichever is sooner)."""
    last = min(exam_date, today + timedelta(days=MAX_DAYS - 1))
    return [today + timedelta(days=i) for i in range((last - today).days + 1)]


def get_topic_stats(subject_id):
    stats = []
    for t in TopicPerformance.query.filter_by(subject_id=subject_id).all():
        total = (t.correct_count or 0) + (t.wrong_count or 0)
        if total:
            stats.append({'topic': t.topic, 'accuracy': round((t.correct_count or 0) * 100 / total),
                          'attempts': total})
    stats.sort(key=lambda s: s['accuracy'])
    return stats


def get_content_sample(subject_id, max_chunks=10):
    chunks = collection.get(where={"subject_id": subject_id})['documents']
    if len(chunks) > max_chunks:
        chunks = random.sample(chunks, max_chunks)
    return [c[:250].replace('\n', ' ') for c in chunks]


def _parse_json_array(text):
    text = text.strip()
    start, end = text.find('['), text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def build_plan(subject, today, hours):
    """Returns a list of {date, title, kind, topic, position}. Raises GeminiError on failure."""
    days = plan_window(subject.exam_date, today)
    per_day = TASKS_PER_DAY.get(hours, 3)

    try:
        content = get_content_sample(subject.id)
    except Exception as e:
        print('PLAN ERROR: ChromaDB read failed:', repr(e))
        raise GeminiError('Document-er content porte parini. Document abar upload kore dekho.')
    if not content:
        raise GeminiError('Ei subject-e kono document text nai. Age text-wala PDF upload koro.')

    stats = get_topic_stats(subject.id)
    if stats:
        weak = "\n".join(f"- {s['topic']}: {s['accuracy']}% ({s['attempts']} ta question)" for s in stats[:10])
    else:
        weak = "Ekhono kono quiz deoa hoyni, tai dubol topic jana nai."

    days_left = (subject.exam_date - today).days
    prompt = f"""Tumi ekjon study planner. Student-er jonno exam porjonto din-ba-din ekta study plan banao.

Subject: {subject.subject_name}
Aj-er tarikh: {today.isoformat()}
Exam-er tarikh: {subject.exam_date.isoformat()} ({days_left} din baki)
Student protidin proay {hours} ghonta porte pare.
Plan-er din gulo: {", ".join(d.isoformat() for d in days)}

Student-er topic-wise performance (quiz theke, kom accuracy mane dubol):
{weak}

Student-er document theke kichu nomuna:
{chr(10).join('- ' + c for c in content)}

Niyom:
- Dubol topic gulo age-r din gulo-te rakho, ar exam-er kache abar revise rakho.
- Prottek din-e {per_day} ta-r beshi task rakho na.
- kind hobe: "read" (notun poRa), "revise" (abar poRa), "practice" (nijei likhe ba problem solve kora), "quiz" (quiz deya).
- Shesh 1-2 din-e shudhu revise ar quiz rakho.
- Shudhu document-e thaka topic use koro, baire theke topic add korona.
- title English-e, 80 character-er moddhe, ki korte hobe seta bujhay.
- topic field-e topic-er naam dao (quiz-er topic-er shathe milay), na thakle "".

Shudhu ei JSON array return koro, r kichu na:
[{{"date": "YYYY-MM-DD", "tasks": [{{"title": "...", "kind": "revise", "topic": "..."}}]}}]
"""

    text = generate_text(prompt, json_mode=True, timeout=90)
    try:
        data = _parse_json_array(text)
    except Exception as e:
        print('PLAN PARSE ERROR:', repr(e), '|', text[:200])
        raise GeminiError('Plan-er format bhul eshechhe. Abar try koro.')

    valid_dates = {d.isoformat(): d for d in days}
    items = []
    for day in data if isinstance(data, list) else []:
        d = valid_dates.get(str(day.get('date', '')))
        if not d:
            continue
        for position, task in enumerate((day.get('tasks') or [])[:per_day]):
            title = str(task.get('title', '')).strip()[:200]
            if not title:
                continue
            kind = task.get('kind') if task.get('kind') in KINDS else 'revise'
            items.append({'date': d, 'title': title, 'kind': kind,
                          'topic': str(task.get('topic') or '').strip()[:200], 'position': position})

    if not items:
        raise GeminiError('AI plan toiri korte parlo na. Abar try koro.')
    return items
