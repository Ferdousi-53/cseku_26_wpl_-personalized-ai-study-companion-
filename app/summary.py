"""Premium: an AI study summary of the student's documents."""
import json
import random

from app.gemini import generate_text, GeminiError
from app.rag import collection

MAX_CHARS = 24000


def _parse_object(text):
    text = text.strip()
    start, end = text.find('{'), text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _clean_list(value, limit):
    if not isinstance(value, list):
        return []
    return [x for x in value if x][:limit]


def build_summary(subject_id, document_ids):
    """Returns {overview, key_points, terms:[{term, meaning}], exam_questions}."""
    try:
        chunks = collection.get(where={"$and": [
            {"subject_id": subject_id},
            {"document_id": {"$in": document_ids}},
        ]})['documents']
    except Exception as e:
        print('SUMMARY ERROR: ChromaDB read failed:', repr(e))
        raise GeminiError('Document-er content porte parini. Document abar upload kore dekho.')
    if not chunks:
        raise GeminiError('Select kora document-e kono text paoa jayni. Text-wala PDF upload koro.')

    text, used = '', 0
    order = list(range(len(chunks)))
    if len(chunks) > 40:
        order = sorted(random.sample(order, 40))
    for i in order:
        if used + len(chunks[i]) > MAX_CHARS:
            break
        text += chunks[i] + '\n\n'
        used += len(chunks[i])

    prompt = f"""Niche deya study content-er ekta revision summary banao.
Shudhu ei content-er upor base koro, baire theke kichu add korona.

Content:
{text}

Shudhu ei JSON object return koro, r kichu na:
{{
  "overview": "3-4 line-e puro bishoy-er shar kotha",
  "key_points": ["5 theke 10 ta gurutter bishoy, prottek ta ek-dui line"],
  "terms": [{{"term": "important shobdo", "meaning": "choto, shohoj ortho"}}],
  "exam_questions": ["5 ta question ja exam-e ashte pare"]
}}
"terms" e 5 theke 10 ta dao."""
    raw = generate_text(prompt, json_mode=True, timeout=90)
    try:
        data = _parse_object(raw)
    except Exception as e:
        print('SUMMARY PARSE ERROR:', repr(e), '|', raw[:200])
        raise GeminiError('Summary-r format bhul eshechhe. Abar try koro.')

    terms = []
    for t in data.get('terms') or []:
        if isinstance(t, dict) and t.get('term'):
            terms.append({'term': str(t['term']), 'meaning': str(t.get('meaning', ''))})
    result = {
        'overview': str(data.get('overview', '')).strip(),
        'key_points': [str(x) for x in _clean_list(data.get('key_points'), 12)],
        'terms': terms[:12],
        'exam_questions': [str(x) for x in _clean_list(data.get('exam_questions'), 8)],
    }
    if not (result['overview'] or result['key_points']):
        raise GeminiError('AI khali summary dilo. Abar try koro.')
    return result
