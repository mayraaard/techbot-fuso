import csv
import os
import re
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

judge_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

DEMO_QUERIES = [
    "Fuso Fighter overheat di tanjakan panjang, radiator dan thermostat sudah dicek normal. Apa yang harus dicek selanjutnya?",
    "Canter bunyi ketukan halus saat cold start, hilang setelah mesin warm-up 10 menit. Apakah ini perlu tindakan segera?",
    "Berapa interval penggantian filter udara untuk Fighter X FN61 FSL yang beroperasi di area tambang?",
    "Fighter power loss bertahap 2 bulan, sudah ganti filter udara dan filter BBM primer tapi tidak membaik. Apa yang harus dicek?",
    "Kendaraan keluar asap putih terus setelah perjalanan jauh dari daerah terpencil, kompresi normal. Apa penyebabnya?",
]


# ─── Parse ────────────────────────────────────────────────────────────────────

def parse_judge_response(response_text: str) -> dict:
    """Parse output judge LLM. Return {"score": int, "reason": str}."""
    score_match = re.search(r"SKOR:\s*([1-5])", response_text)
    reason_match = re.search(r"ALASAN:\s*(.+?)(?=\nSKOR:|\Z)", response_text, re.DOTALL)

    if not score_match:
        return {"score": 0, "reason": "Parse error: pola SKOR tidak ditemukan"}

    score = int(score_match.group(1))
    reason = reason_match.group(1).strip() if reason_match else response_text.strip()[:200]
    return {"score": score, "reason": reason}


# ─── 4 Fungsi Evaluasi ────────────────────────────────────────────────────────

def eval_faithfulness(context: str, answer: str) -> dict:
    prompt = f"""Kamu adalah evaluator sistem RAG yang objektif.

Nilai FAITHFULNESS dari jawaban berikut.
Faithfulness mengukur apakah jawaban HANYA menggunakan informasi dari konteks yang diberikan, tanpa menambahkan pengetahuan dari luar.

Konteks dokumen:
{context}

Jawaban yang dievaluasi:
{answer}

Berikan skor 1-5:
1 = Jawaban banyak mengandung informasi yang tidak ada di konteks
2 = Jawaban sebagian besar dari konteks tapi ada beberapa info dari luar
3 = Jawaban mayoritas dari konteks dengan sedikit tambahan kecil
4 = Jawaban hampir sepenuhnya dari konteks, penyimpangan minimal
5 = Jawaban 100% berdasarkan konteks, tidak ada info dari luar

Jawab dengan format persis:
SKOR: [angka 1-5]
ALASAN: [satu kalimat penjelasan]"""

    response = judge_llm.invoke([HumanMessage(content=prompt)])
    return parse_judge_response(response.content)


def eval_context_relevance(query: str, context: str) -> dict:
    prompt = f"""Kamu adalah evaluator sistem RAG yang objektif.

Nilai CONTEXT RELEVANCE dari dokumen yang di-retrieve.
Context Relevance mengukur apakah dokumen-dokumen yang diambil dari knowledge base relevan untuk menjawab pertanyaan.

Pertanyaan:
{query}

Konteks dokumen yang di-retrieve:
{context}

Berikan skor 1-5:
1 = Dokumen yang di-retrieve sama sekali tidak relevan dengan pertanyaan
2 = Sebagian kecil dokumen relevan, mayoritas tidak
3 = Sebagian dokumen relevan, sebagian tidak
4 = Mayoritas dokumen relevan dengan pertanyaan
5 = Semua dokumen yang di-retrieve sangat relevan dengan pertanyaan

Jawab dengan format persis:
SKOR: [angka 1-5]
ALASAN: [satu kalimat penjelasan]"""

    response = judge_llm.invoke([HumanMessage(content=prompt)])
    return parse_judge_response(response.content)


def eval_answer_relevancy(query: str, answer: str) -> dict:
    prompt = f"""Kamu adalah evaluator sistem RAG yang objektif.

Nilai ANSWER RELEVANCY dari jawaban berikut.
Answer Relevancy mengukur apakah jawaban benar-benar menjawab pertanyaan yang diajukan — bukan hanya relevan secara topik, tapi secara langsung address pertanyaannya.

Pertanyaan:
{query}

Jawaban yang dievaluasi:
{answer}

Berikan skor 1-5:
1 = Jawaban sama sekali tidak menjawab pertanyaan
2 = Jawaban sedikit menyinggung pertanyaan tapi tidak menjawab
3 = Jawaban menjawab sebagian pertanyaan
4 = Jawaban menjawab pertanyaan dengan baik, sedikit kurang spesifik
5 = Jawaban langsung dan lengkap menjawab pertanyaan

Jawab dengan format persis:
SKOR: [angka 1-5]
ALASAN: [satu kalimat penjelasan]"""

    response = judge_llm.invoke([HumanMessage(content=prompt)])
    return parse_judge_response(response.content)


def eval_groundedness(context: str, answer: str) -> dict:
    prompt = f"""Kamu adalah evaluator sistem RAG yang objektif.

Nilai GROUNDEDNESS dari jawaban berikut.
Groundedness mengukur apakah setiap klaim spesifik dalam jawaban bisa dilacak ke bagian tertentu dari dokumen konteks — lebih granular dari faithfulness.

Konteks dokumen:
{context}

Jawaban yang dievaluasi:
{answer}

Berikan skor 1-5:
1 = Sebagian besar klaim tidak bisa dilacak ke dokumen
2 = Beberapa klaim bisa dilacak, banyak yang tidak
3 = Separuh klaim bisa dilacak ke dokumen
4 = Mayoritas klaim bisa dilacak ke dokumen dengan jelas
5 = Setiap klaim spesifik bisa dilacak ke bagian dokumen yang jelas

Jawab dengan format persis:
SKOR: [angka 1-5]
ALASAN: [satu kalimat penjelasan]"""

    response = judge_llm.invoke([HumanMessage(content=prompt)])
    return parse_judge_response(response.content)


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_evaluation():
    from retriever import get_ensemble_retriever
    from llm import ask

    print("=" * 60)
    print("EVALUASI OFFLINE — TechBot Fuso")
    print("Metrik: Faithfulness, Context Relevance, Answer Relevancy, Groundedness")
    print("Judge: gemini-2.5-flash-lite")
    print("=" * 60)

    retriever = get_ensemble_retriever()
    results = []

    for i, query in enumerate(DEMO_QUERIES, 1):
        print(f"\nQuery {i}: {query[:70]}...")
        print("  Generating answer...")

        result = ask(query, retriever)
        answer = result["answer"]
        context = result["context"]

        print("  Evaluating...")
        time.sleep(2)

        faith = eval_faithfulness(context, answer)
        time.sleep(1)
        ctx_rel = eval_context_relevance(query, context)
        time.sleep(1)
        ans_rel = eval_answer_relevancy(query, answer)
        time.sleep(1)
        ground = eval_groundedness(context, answer)

        print(f"  Faithfulness     : {faith['score']}/5 — {faith['reason']}")
        print(f"  Context Relevance: {ctx_rel['score']}/5 — {ctx_rel['reason']}")
        print(f"  Answer Relevancy : {ans_rel['score']}/5 — {ans_rel['reason']}")
        print(f"  Groundedness     : {ground['score']}/5 — {ground['reason']}")

        results.append({
            "query": query,
            "answer_preview": answer[:100] + "...",
            "faithfulness": faith["score"],
            "faithfulness_reason": faith["reason"],
            "context_relevance": ctx_rel["score"],
            "context_relevance_reason": ctx_rel["reason"],
            "answer_relevancy": ans_rel["score"],
            "answer_relevancy_reason": ans_rel["reason"],
            "groundedness": ground["score"],
            "groundedness_reason": ground["reason"],
        })

        time.sleep(3)

    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_ctx = sum(r["context_relevance"] for r in results) / len(results)
    avg_ans = sum(r["answer_relevancy"] for r in results) / len(results)
    avg_ground = sum(r["groundedness"] for r in results) / len(results)

    print("\n" + "=" * 60)
    print("RINGKASAN:")
    print(f"  Avg Faithfulness     : {avg_faith:.1f}/5")
    print(f"  Avg Context Relevance: {avg_ctx:.1f}/5")
    print(f"  Avg Answer Relevancy : {avg_ans:.1f}/5")
    print(f"  Avg Groundedness     : {avg_ground:.1f}/5")
    print("=" * 60)

    csv_file = "eval_results.csv"
    fieldnames = list(results[0].keys())
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nHasil disimpan ke: {csv_file}")
    return results


if __name__ == "__main__":
    run_evaluation()
