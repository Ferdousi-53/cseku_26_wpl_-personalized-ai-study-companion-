import json
import random
from app.rag import collection, search_chunks
from app.gemini import generate_text, GeminiError
from app.models import TopicPerformance


def get_weak_topics(subject_id, limit=5, threshold=70):
    """Topic names where the student's accuracy is below `threshold`, weakest first."""
    rows = []
    for t in TopicPerformance.query.filter_by(subject_id=subject_id).all():
        total = (t.correct_count or 0) + (t.wrong_count or 0)
        if total == 0:
            continue
        accuracy = (t.correct_count or 0) * 100 / total
        if accuracy < threshold:
            rows.append((accuracy, t.topic))
    rows.sort()
    return [name for _, name in rows[:limit]]


def get_selected_content(subject_id, document_ids, max_chunks=15):
    results = collection.get(
        where={"$and": [
            {"subject_id": subject_id},
            {"document_id": {"$in": document_ids}}
        ]}
    )
    chunks = results['documents']

    if len(chunks) > max_chunks:
        chunks = random.sample(chunks, max_chunks)

    return chunks


def get_focus_content(subject_id, document_ids, topics, max_chunks=15):
    """Pulls the chunks most related to each weak topic."""
    chunks, seen = [], set()
    for topic in topics:
        for chunk in search_chunks(topic, subject_id, document_ids=document_ids, n_results=4):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)
    return chunks[:max_chunks]


def _parse_quiz_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find('['), text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def generate_quiz(subject_id, document_ids, num_questions=5, focus_topics=None, exam=False):
    try:
        chunks = []
        if focus_topics:
            chunks = get_focus_content(subject_id, document_ids, focus_topics)
        if not chunks:
            chunks = get_selected_content(subject_id, document_ids)
    except Exception as e:
        print("QUIZ ERROR: ChromaDB theke content porte parini:", repr(e))
        raise GeminiError("Document-er content porte parini. Document abar upload kore dekho.")

    if not chunks:
        raise GeminiError("Select kora document-e kono text paoa jayni. Document delete kore text-wala PDF abar upload koro.")

    context = "\n\n".join(chunks)

    if focus_topics:
        topic_rule = (
            "Student ei topic gulo-te dubol: " + ", ".join(focus_topics) + ".\n"
            "Ei topic gulor upor focus kore question banao. Prottek question-er \"topic\" field-e "
            "ei naam gulor ekta ekdom hubohu (spelling soho) likho."
        )
    else:
        topic_rule = "Prottek question-er shathe ekta choto \"topic\" (2-4 shobdo-r concept naam) dao, jeta bujhay question ta kon bishoy theke ashche."

    exam_rule = ""
    if exam:
        exam_rule = (
            "Eta ekta real exam-er moto: question gulo medium theke hard level-er hobe, "
            "kichu question e concept apply korte hobe (shudhu mukhosto noy), "
            "ar content-er alada alada onsho theke question nao.\n"
        )

    prompt = f"""Niche deya content theke {num_questions} ta multiple choice question (MCQ) banao.
{exam_rule}Shudhu ei content-er upor base kore question banao, onno kono baire theke information add korona.

Content:
{context}

{topic_rule}
Prottek question-er shathe ekta "explanation" dao: 1-2 chhoto line-e bujhao keno sothik uttor ta sothik. Explanation question-er bhashatei likho.

Shudhu ei JSON array ta return koro, r kono text, explanation ba markdown code fence (```) chara:

[
  {{
    "question": "question text",
    "options": ["option A", "option B", "option C", "option D"],
    "correct_index": 0,
    "topic": "short topic name",
    "explanation": "why the correct option is right"
  }}
]
"""

    text = generate_text(prompt, json_mode=True)

    try:
        quiz_data = _parse_quiz_json(text)
    except Exception as e:
        print("QUIZ PARSE ERROR:", repr(e), "|", text[:200])
        raise GeminiError("Quiz-er format bhul eshechhe. Abar try koro.")

    if not isinstance(quiz_data, list) or not quiz_data:
        raise GeminiError("AI khali quiz dilo. Abar try koro.")

    return quiz_data
