# TechBot Fuso — KTB Field Technician Assistant

## Deskripsi
RAG chatbot untuk teknisi junior bengkel resmi KTB (Mitsubishi Fuso).
Membantu diagnosis kendaraan berdasarkan knowledge base internal.

## Stack
- Python + Streamlit (UI + deployment)
- LangChain (RAG orchestration)
- Google Gemini 2.5 Flash Lite (LLM) + gemini-embedding-001 (embedding)
- ChromaDB (vector store lokal, di-commit ke GitHub)
- python-docx (baca file .docx)
- SQLite (monitoring log)

## Struktur file
- app.py — Streamlit UI, import dari modul lain
- ingest.py — load docs/, chunk, embed, simpan ke chroma_db/
- retriever.py — load ChromaDB, fungsi similarity search
- llm.py — setup Gemini, system prompt, fungsi generate jawaban
- monitoring.py — logging response time + token usage ke SQLite
- docs/ — 13 file .docx knowledge base
- chroma_db/ — hasil ingestion, di-commit ke GitHub

## Kendaraan yang dicakup
- Fuso Canter FE 74 HD
- Fuso Fighter X FN61 FSL

## Dokumen knowledge base
4 file explicit knowledge (SOP + troubleshooting) dan
9 file case report teknisi senior (tacit knowledge).

## Ketentuan penting
- API key dari environment variable GOOGLE_API_KEY, tidak pernah hardcoded
- ingest.py dijalankan manual sekali, hasilnya di-commit. Tidak dijalankan otomatis dari app.py
- Chunking strategy: section-based, satu case report = satu chunk (tidak dipotong di tengah)
- Output bahasa Indonesia
- Setiap jawaban harus menyebut sumber dokumen (citation)







# TechBot Fuso — KTB Field Technician Assistant

## Deskripsi Proyek
RAG chatbot untuk teknisi junior bengkel resmi KTB (Mitsubishi Fuso).
Membantu diagnosis kendaraan berdasarkan dua lapisan knowledge base:
- **Explicit knowledge**: SOP dan troubleshooting guide resmi
- **Tacit knowledge**: catatan lapangan teknisi senior, case report, lesson learned

Tagline: "Selama 18 tahun, knowledge terbaik KTB ada di kepala teknisi senior. Sekarang, ada di sini juga."

## Target User
Teknisi junior bengkel resmi KTB dengan pengalaman < 5 tahun. Tahu prosedur standar, tapi belum punya intuisi lapangan untuk edge cases yang tidak tercakup di manual.

## Kendaraan yang Dicakup (Scope PoC)
- **Fuso Canter FE 74 HD** — GVW 7.500 kg, mesin 4D34-2AT5, 4 silinder
- **Fuso Fighter X FN61 FSL** — GVW 26.000 kg, mesin 6D16-TLB, 6 silinder

---

## Tech Stack

| Library | Versi | Fungsi |
|---|---|---|
| `streamlit` | latest | UI + deployment ke Streamlit Community Cloud |
| `langchain` | latest | Orchestration RAG pipeline |
| `langchain-google-genai` | latest | Integrasi Gemini LLM + embedding |
| `langchain-community` | latest | Document loaders, BM25Retriever |
| `chromadb` | latest | Vector store lokal (di-commit ke GitHub) |
| `rank-bm25` | latest | Keyword retriever untuk hybrid search |
| `python-docx` | latest | Baca file .docx |
| `python-dotenv` | latest | Load environment variable dari .env |

**Python: 3.11+**

**LLM**: Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`)
**Embedding**: `gemini-embedding-001` (multilingual, support Bahasa Indonesia)
**API Key**: satu Google API key untuk keduanya via `GOOGLE_API_KEY`

---

## Struktur File

```
techbot-fuso/
├── app.py              ← Streamlit UI, import dari modul lain, TIDAK jalankan ingest
├── ingest.py           ← Load docs/, chunk, embed, simpan ke chroma_db/
├── retriever.py        ← Load ChromaDB + BM25, bangun EnsembleRetriever
├── llm.py              ← Setup Gemini, system prompt, fungsi generate jawaban
├── monitoring.py       ← Logging response time + token usage ke SQLite
├── docs/               ← 13 file .docx knowledge base
├── chroma_db/          ← Hasil ingestion — DI-COMMIT ke GitHub
├── .env                ← API key — TIDAK di-commit (ada di .gitignore)
├── .env.example        ← Template kosong — di-commit
├── requirements.txt    ← Semua dependencies
└── README.md
```

**Aturan penting:**
- `ingest.py` dijalankan MANUAL sekali di lokal, hasilnya (`chroma_db/`) di-commit ke GitHub
- `app.py` hanya LOAD ChromaDB yang sudah ada — tidak pernah jalankan ingest ulang
- Tidak ada API key yang hardcoded di manapun

---

## Dokumen Knowledge Base (13 file .docx di folder `docs/`)

### Explicit Knowledge — 4 file
| Filename | Isi | Model |
|---|---|---|
| `sop_canter_fe74hd.docx` | Service intervals, filter replacement, pre-trip checklist, extreme condition guide | Canter FE 74 HD |
| `sop_fighter_x_fn61fsl.docx` | Service intervals, filter replacement, pre-trip checklist, extreme condition guide | Fighter X FN61 FSL |
| `troubleshooting_canter_fe74hd.docx` | Overheating (8 steps), starting failure, abnormal noise, power loss, fuel/smoke | Canter FE 74 HD |
| `troubleshooting_fighter_x_fn61fsl.docx` | Overheating (9 steps incl. turbo), starting failure, abnormal noise, power loss, fuel/smoke | Fighter X FN61 FSL |

### Tacit Knowledge — 9 file (Case Reports)
| Filename | Kasus | Model |
|---|---|---|
| `case_01_canter_cold_start_noise_timing_chain.docx` | Cold start noise → timing chain tensioner (bukan bearing) | Canter |
| `case_02_canter_hard_starting_udara_di_bbm.docx` | Hard starting → micro-crack pada low-pressure fuel hose | Canter |
| `case_03_canter_brake_fade_turunan_panjang.docx` | Brake fade di turunan → teknik mengemudi (bukan kerusakan) | Canter |
| `case_04_fighter_overheat_oring_thermostat_housing.docx` | Overheat tanjakan → O-ring thermostat housing bergeser | Fighter X |
| `case_05_fighter_power_loss_filter_bbm_sekunder.docx` | Power loss bertahap → filter BBM sekunder 95.000 km tidak diganti | Fighter X |
| `case_06_fighter_vibrasi_balance_weight_propshaft.docx` | Vibrasi 65-70 km/h → balance weight propshaft terlepas | Fighter X |
| `case_07_fighter_asap_putih_air_biasa_coolant.docx` | Asap putih → coolant diganti air biasa di Papua | Fighter X |
| `case_08_umum_keausan_dini_intake_hose_retak.docx` | Keausan mesin dini → intake hose retak bypass filter | Lintas model |
| `case_09_umum_mesin_mati_solar_terkontaminasi_air.docx` | Mesin mati mendadak → solar terkontaminasi air dari SPBU terpencil | Lintas model |

Setiap case report memiliki struktur: info kasus → keluhan pengemudi → yang sudah dicek → temuan aktual → catatan lapangan teknisi senior (first person) → lesson learned.

---

## Chunking Strategy

**Strategi: Hybrid chunking** — dua pendekatan berbeda untuk dua jenis dokumen.

### Case Reports (9 file) → Document-level chunking
**Satu file = satu chunk utuh.**

Alasan: Case report adalah narasi yang tidak bisa dipotong. Mulai dari keluhan sampai lesson learned adalah satu unit knowledge yang harus self-contained. Kalau dipotong di tengah (misal fixed-size 500 karakter), chunk kedua akan berisi "temuan" tanpa tahu "masalahnya apa" — retrieval jadi tidak akurat.

Ukuran: tiap case report ~300-500 kata (~1500-2500 karakter) — jauh di bawah limit 2048 token `text-embedding-004`.

### SOP/Troubleshooting (4 file) → Section-based chunking
**Dipecah per heading/section.**

Alasan: Dokumen ini lebih besar dari case report dan berisi beberapa topik berbeda (overheating, starting failure, power loss, dll). Setiap section adalah unit mandiri — teknisi tanya satu topik, bukan seluruh dokumen. Heading dokumen sudah menjadi batas natural antar knowledge unit.

Contoh: `troubleshooting_fighter_x_fn61fsl.docx` → 5 chunk (overheating, starting failure, abnormal noise, power loss, fuel/smoke).

### Metadata setiap chunk
Setiap chunk harus diberi metadata:
```python
metadata = {
    "source": filename,           # nama file asli
    "doc_type": "case_report",    # atau "sop" / "troubleshooting"
    "vehicle_model": "Fighter X", # atau "Canter" / "Lintas model"
    "chunk_id": "case_04"         # identifier unik
}
```

---

## Retrieval Strategy: Hybrid Search

**Menggunakan `EnsembleRetriever` dari LangChain** — kombinasi ChromaDB (semantic) + BM25 (keyword).

```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# Semantic retriever dari ChromaDB
chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Keyword retriever dari semua chunks
bm25_retriever = BM25Retriever.from_documents(all_chunks)
bm25_retriever.k = 4

# Hybrid: 50% keyword, 50% semantic
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, chroma_retriever],
    weights=[0.5, 0.5]
)
```

---

## LLM Integration & Prompt Engineering

**Model**: `gemini-2.5-flash-lite`
**Output language**: Bahasa Indonesia

System prompt harus:
1. Mengikat jawaban ke dokumen yang di-retrieve (bukan dari memory model)
2. Mewajibkan citation — sebutkan nama file sumber
3. Kalau tidak ada informasi relevan di dokumen, katakan tidak ada — jangan mengarang

Contoh struktur system prompt:
```
Kamu adalah asisten teknis untuk teknisi bengkel resmi Fuso KTB.
Jawab HANYA berdasarkan dokumen konteks yang diberikan.
Setiap jawaban harus menyebutkan sumber dokumen (contoh: "Berdasarkan Case #04" atau "Berdasarkan SOP Fighter X").
Jika informasi tidak ada dalam konteks, katakan: "Informasi ini tidak tersedia dalam knowledge base."
Jangan menambahkan informasi dari luar dokumen yang diberikan.
Jawab dalam Bahasa Indonesia.
```

---

## Monitoring

Catat minimal 6 metrik per query ke SQLite (`monitoring.db`):
1. **Avg Response time** — waktu dari query masuk sampai jawaban keluar (detik)
2. **Token usage** — input token + output token dari Gemini API response
3. **Query Count**
4. **Estimated Cost**
5. **Most Referenced Source**
6. **Fallback Rate**

Tampilkan di tab 2 Streamlit.

---

## Demo Queries (untuk live demo)

Lima query ini harus menghasilkan jawaban relevan dengan citation yang jelas:

1. "Fuso Fighter overheat di tanjakan panjang, radiator dan thermostat sudah dicek normal, apa yang harus dicek selanjutnya?"
   → Expected: case_04 (O-ring thermostat housing) + troubleshooting_fighter (step 7-9)

2. "Canter bunyi ketukan halus saat cold start, hilang setelah mesin warm-up 10 menit. Apakah ini perlu tindakan segera?"
   → Expected: case_01 (timing chain tensioner) + troubleshooting_canter (cold start noise)

3. "Berapa interval penggantian filter udara untuk Fighter X FN61 FSL yang beroperasi di area tambang?"
   → Expected: sop_fighter (kondisi ekstrem: cek setiap hari, ganti setiap 5.000 km)

4. "Fighter power loss bertahap 2 bulan, sudah ganti filter udara dan filter BBM primer tapi tidak membaik. Apa yang harus dicek?"
   → Expected: case_05 (filter BBM sekunder) + troubleshooting_fighter (power loss section)

5. "Kendaraan keluar asap putih terus setelah perjalanan jauh dari daerah terpencil, kompresi normal. Apa penyebabnya?"
   → Expected: case_07 (air biasa sebagai coolant) + troubleshooting_fighter (warna asap)

---

## Deployment

**Platform**: Streamlit Community Cloud (gratis, deploy dari GitHub)
**URL publik** harus aktif saat presentasi.

Setup secrets di Streamlit Cloud:
```toml
# Di Streamlit Cloud > App Settings > Secrets
GOOGLE_API_KEY = "isi_api_key_di_sini"
```

Di kode, baca dengan:
```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
```

---

## Rubrik Penilaian (referensi prioritas)

| Aspek | Poin | Catatan |
|---|---|---|
| RAG Pipeline | 25 | Chunking strategy harus bisa dijelaskan — pakai penjelasan di atas |
| Problem Framing | 20 | Sudah strong — fokus business framing saat presentasi |
| LLM Integration + Prompt Engineering | 15 | No hallucination, jawaban terikat dokumen, ada citation |
| Deployment | 15 | Public URL aktif, tidak ada fatal error, UI intuitif |
| Monitoring | 15 | Min. 2 metrik otomatis, bisa ditunjukkan saat demo |
| Kode + Dokumentasi | 10 | README lengkap, tidak ada hardcoded credentials |

---
