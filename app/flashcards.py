"""Makes flashcards from the student's documents with the AI."""
import json
import random

from app.gemini import generate_text, GeminiError
from app.rag import collection

MAX_CARDS = 20


def _parse_array(text):
    text = text.strip()
    start, end = text.find('['), text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def build_cards(subject_id, document_ids, count, existing_fronts=None):
    """Returns a list of {front, back, topic}. Raises GeminiError on failure."""
    count = max(1, min(count, MAX_CARDS))
    try:
        chunks = collection.get(where={"$and": [
            {"subject_id": subject_id},
            {"document_id": {"$in": document_ids}},
        ]})['documents']
    except Exception as e:
        print('CARDS ERROR: ChromaDB read failed:', repr(e))
        raise GeminiError('Document-er content porte parini. Document abar upload kore dekho.')
    if not chunks:
        raise GeminiError('Select kora document-e kono text paoa jayni. Text-wala PDF upload koro.')
    if len(chunks) > 12:
        chunks = random.sample(chunks, 12)

    avoid = ''
    if existing_fronts:
        avoid = "\nEi question gulo age-i ache, abar korona:\n" + "\n".join('- ' + f[:100] for f in existing_fronts[:30]) + "\n"

    prompt = f"""Niche deya content theke {count} ta flashcard banao revision-er jonno.
Shudhu ei content-er upor base koro, baire theke kichu add korona.

Content:
{chr(10).join(chunks)}
{avoid}
Niyom:
- "front": ekta chhoto question ba term (ek line).
- "back": chhoto, shothik uttor (1-3 line), content theke.
- "topic": 2-4 shobdo-er concept naam.
- Card gulo alada alada concept-er hobe, ekই jinish repeat korona.

Shudhu ei JSON array return koro, r kichu na:
[{{"front": "...", "back": "...", "topic": "..."}}]
"""
    text = generate_text(prompt, json_mode=True, timeout=90)
    try:
        data = _parse_array(text)
    except Exception as e:
        print('CARDS PARSE ERROR:', repr(e), '|', text[:200])
        raise GeminiError('Card-er format bhul eshechhe. Abar try koro.')

    cards, seen = [], {f.strip().lower() for f in (existing_fronts or [])}
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        front = str(item.get('front', '')).strip()[:500]
        back = str(item.get('back', '')).strip()[:1000]
        if not front or not back or front.lower() in seen:
            continue
        seen.add(front.lower())
        cards.append({'front': front, 'back': back, 'topic': str(item.get('topic') or '').strip()[:200]})
    if not cards:
        raise GeminiError('AI kono card toiri korte parlo na. Abar try koro.')
    return cards[:count]
