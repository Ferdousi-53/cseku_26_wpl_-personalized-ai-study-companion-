from app.rag import search_chunks
from app.gemini import generate_text, GeminiError


def _short(text, limit=600):
    text = (text or '').strip()
    return text if len(text) <= limit else text[:limit] + '...'


def get_ai_answer(question, subject_id, document_ids=None, history=None):
    """Returns (answer, sources). On an AI/service error returns (message, None)."""
    history = history or []

    # A short follow-up like "ota ektu simple kore bolo" has no topic words,
    # so search with the previous question as well.
    search_query = question
    if history and len(question.split()) < 8:
        last_user = next((m['text'] for m in reversed(history) if m['role'] == 'user'), '')
        search_query = f"{last_user} {question}".strip()

    relevant_chunks = search_chunks(search_query, subject_id, document_ids=document_ids, n_results=3)

    if not relevant_chunks:
        return "Tomar uploaded document-e ei question-er relevant kono information pawa jayni.", []

    context = "\n\n".join(relevant_chunks)

    conversation = ""
    if history:
        lines = [f"{'Student' if m['role'] == 'user' else 'Tutor'}: {_short(m['text'])}" for m in history]
        conversation = "Age-r kothopokothon:\n" + "\n".join(lines) + "\n\n"

    prompt = f"""Tumi ekjon helpful study tutor. Niche deya context use kore student-er question-er answer dao.
Context er baire kichu bolo na. Simple bhasay bujhiye dao.
Student-er notun question ta age-r kothopokothon-er shathe jora hote pare (jemon "ota", "arektu simple kore bolo"), seta bujhe uttor dao.

{conversation}Document theke paoa context:
{context}

Student-er notun question: {question}

Answer:"""

    try:
        answer = generate_text(prompt)
    except GeminiError as e:
        return e.user_message, None

    return answer, relevant_chunks
