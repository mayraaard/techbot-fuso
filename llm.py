"""
llm.py — Setup Gemini, system prompt, fungsi generate jawaban.
Di-import oleh app.py dan eval_offline.py.
"""

import os
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

load_dotenv()

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Kamu adalah TechBot Fuso, asisten teknis untuk teknisi bengkel resmi KTB (Krama Yudha Tiga Berlian Motors).

ATURAN MUTLAK:
1. Jawab HANYA berdasarkan dokumen konteks yang diberikan di bawah.
2. Jangan menambahkan informasi dari pengetahuan umum atau memori model.
3. Jika pertanyaan menyebutkan model kendaraan spesifik (Canter atau Fighter X), gunakan HANYA informasi dari dokumen model tersebut. Abaikan informasi model kendaraan lain yang ada dalam konteks.
4. Setiap jawaban HARUS menyebutkan sumber dokumen. Gunakan format:
   - Untuk case report: "Berdasarkan Case #XX — [judul kasus]"
   - Untuk troubleshooting: "Berdasarkan Panduan Troubleshooting [model kendaraan], Bagian [nama section]"
   - Untuk SOP: "Berdasarkan SOP [model kendaraan], Bagian [nama section]"
5. Jika informasi tidak ditemukan dalam konteks: jawab dengan "Informasi ini tidak tersedia dalam knowledge base TechBot Fuso. Silakan konsultasikan dengan teknisi senior atau hubungi KTB technical support."
6. Jawab dalam Bahasa Indonesia yang jelas dan teknis.
7. Untuk pertanyaan diagnosis: berikan langkah-langkah secara berurutan jika tersedia di dokumen.
8. Berikan jawaban yang lengkap dan komprehensif. Jika ada beberapa dokumen relevan dalam konteks, gunakan dan sebutkan SEMUA sumber tersebut dalam jawaban — jangan hanya pakai satu sumber."""
# ─── Lazy LLM Init ────────────────────────────────────────────────────────────

_llm: ChatGoogleGenerativeAI | None = None


def _get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY tidak ditemukan. "
                "Set di file .env atau Streamlit Cloud Secrets."
            )
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.1,
            google_api_key=api_key,
        )
    return _llm


# ─── Main Function ────────────────────────────────────────────────────────────
def _detect_vehicle(query: str, chat_history: list = None) -> str | None:
    q = query.lower()
    if "fighter" in q:
        return "Fighter X"
    elif "canter" in q:
        return "Canter"

    # Query tidak menyebut model — cek history terakhir
    if chat_history:
        for msg in reversed(chat_history[-6:]):
            content = msg.get("content", "").lower()
            if "fighter" in content:
                return "Fighter X"
            elif "canter" in content:
                return "Canter"

    return None  # query umum, tidak difilter

def ask(query: str, retriever, chat_history: list = None) -> dict:
    """Retrieve konteks + generate jawaban. Return dict lengkap untuk monitoring dan eval."""
    start = time.time()

    # 1. Retrieve
    docs = retriever.invoke(query)

    # Filter by vehicle model jika terdeteksi
    vehicle = _detect_vehicle(query, chat_history)
    if vehicle:
        filtered = [
            d for d in docs
            if d.metadata.get("vehicle_model") in (vehicle, "Lintas model")
        ]
        if filtered:  # pakai filter hanya kalau hasilnya tidak kosong
            docs = filtered

    # 2. Gabungkan page_content menjadi satu context string
    context_parts = []
    for doc in docs:
        meta = doc.metadata
        doc_type = meta.get("doc_type", "")
        if doc_type == "case_report":
            label = f"[CASE REPORT: {meta.get('chunk_id', '').upper()}]"
        elif doc_type == "troubleshooting":
            label = f"[PANDUAN TROUBLESHOOTING: {meta.get('vehicle_model', '')} — {meta.get('section', '')}]"
        elif doc_type == "sop":
            label = f"[SOP: {meta.get('vehicle_model', '')} — {meta.get('section', '')}]"
        else:
            label = f"[SUMBER: {meta.get('source', '')}]"
        context_parts.append(f"{label}\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    # 3. Build messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Sisipkan last 3 pasangan history (kalau ada)
    if chat_history:
        recent = chat_history[-6:]  # 3 pasangan = 6 messages
        for h in recent:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                messages.append(AIMessage(content=h["content"]))

    # HumanMessage terakhir: query sekarang + context dokumen
    messages.append(HumanMessage(content=(
        f"Konteks dari knowledge base:\n\n{context}\n\n"
        f"Pertanyaan teknisi: {query}\n\n"
        f"Catatan: Periksa SEMUA sumber yang tersedia di atas. "
        f"Jika ada [CASE REPORT] dan [PANDUAN TROUBLESHOOTING] yang keduanya relevan, "
        f"kamu HARUS menyebutkan dan menggunakan kedua sumber tersebut dalam jawaban."
    )))

    # 4. Generate
    llm = _get_llm()
    response = llm.invoke(messages)

    # 5. Ambil jawaban dan token usage
    answer: str = response.content
    is_fallback = "tidak tersedia dalam knowledge base" in answer.lower()
    if is_fallback:
        answer = (
            "Informasi ini tidak tersedia dalam knowledge base TechBot Fuso. "
            "Silakan konsultasikan dengan teknisi senior atau hubungi KTB technical support."
        )
    usage = response.usage_metadata or {}
    input_tokens: int = usage.get("input_tokens", 0)
    output_tokens: int = usage.get("output_tokens", 0)

    response_time = round(time.time() - start, 2)

    return {
        "answer": answer,
        "context": context,
        "sources": docs,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens": input_tokens + output_tokens,
        "response_time": response_time,
        "is_fallback": "tidak tersedia dalam knowledge base" in answer.lower(),
    }


# ─── Test ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from retriever import format_sources, get_ensemble_retriever

    retriever = get_ensemble_retriever()
    query = "berapa interval filter udara Fighter X di area tambang?"

    print(f"Query: {query}\n")
    result = ask(query, retriever)

    print("=" * 60)
    print(f"JAWABAN:\n{result['answer']}\n")
    print("=" * 60)
    print(f"response_time : {result['response_time']}s")
    print(f"input_tokens  : {result['input_tokens']}")
    print(f"output_tokens : {result['output_tokens']}")
    print(f"tokens (total): {result['tokens']}")
    print(f"is_fallback   : {result['is_fallback']}")
    print(f"\nSOURCES:")
    for s in format_sources(result["sources"]):
        print(f"  • {s}")
    print(f"\nCONTEXT (300 char pertama):\n{result['context'][:300]}...")
