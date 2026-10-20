import chromadb
from pypdf import PdfReader

chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="study_documents")


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
    return full_text


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def process_document(pdf_path, subject_id, document_id):
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)

    for idx, chunk in enumerate(chunks):
        chunk_id = f"doc{document_id}_chunk{idx}"
        collection.add(
            documents=[chunk],
            metadatas=[{"subject_id": subject_id, "document_id": document_id}],
            ids=[chunk_id]
        )

    return len(chunks)


def search_chunks(query, subject_id, document_ids=None, n_results=3):
    if document_ids:
        where_filter = {"$and": [
            {"subject_id": subject_id},
            {"document_id": {"$in": document_ids}}
        ]}
    else:
        where_filter = {"subject_id": subject_id}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter
    )
    return results['documents'][0] if results['documents'] else []
def delete_document_chunks(document_id):
    collection.delete(where={"document_id": document_id})