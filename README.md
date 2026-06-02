# TechBot Fuso — KTB Field Technician Assistant

> "Selama 18 tahun, knowledge terbaik KTB ada di kepala teknisi senior. Sekarang, ada di sini juga."

RAG chatbot untuk teknisi junior bengkel resmi KTB (Mitsubishi Fuso).
Membantu diagnosis kendaraan berdasarkan dua lapisan knowledge base:
- **Explicit knowledge** — SOP dan troubleshooting guide resmi
- **Tacit knowledge** — catatan lapangan teknisi senior, case report, lesson learned

---

## Kendaraan yang Dicakup

| Model | GVW | Mesin |
|---|---|---|
| Fuso Canter FE 74 HD | 7.500 kg | 4D34-2AT5, 4 silinder |
| Fuso Fighter X FN61 FSL | 26.000 kg | 6D16-TLB, 6 silinder |

---

## Tech Stack

| Library | Fungsi |
|---|---|
| `streamlit` | UI + deployment ke Streamlit Community Cloud |
| `langchain` + `langchain-community` | RAG orchestration, EnsembleRetriever |
| `langchain-google-genai` | Gemini LLM + embedding |
| `chromadb` | Vector store lokal |
| `rank-bm25` | Keyword retriever untuk hybrid search |
| `python-docx` | Baca file `.docx` |
| `python-dotenv` | Load environment variable |
| `plotly` | Chart di tab monitoring |

**Python**: 3.11+  
**LLM**: `gemini-2.5-flash-lite`  
**Embedding**: `gemini-embedding-001`

---

## Struktur File

```
techbot-fuso/
├── app.py              ← Streamlit UI
├── ingest.py           ← Load docs/, chunk, embed, simpan ke chroma_db/
├── retriever.py        ← Load ChromaDB + BM25, bangun EnsembleRetriever
├── llm.py              ← Setup Gemini, system prompt, fungsi generate jawaban
├── monitoring.py       ← Logging response time + token usage ke SQLite
├── eval_offline.py     ← Evaluasi offline RAG pipeline (LLM-as-judge)
├── docs/               ← 13 file .docx knowledge base
├── chroma_db/          ← Hasil ingestion — DI-COMMIT ke GitHub
├── bm25_chunks.json    ← Chunks untuk BM25Retriever — DI-COMMIT ke GitHub
├── .env                ← API key — TIDAK di-commit
├── .env.example        ← Template kosong — di-commit
├── requirements.txt    ← Semua dependencies
└── README.md
```

---

## Setup

### 1. Clone repository

```bash
git clone https://github.com/<username>/techbot-fuso.git
cd techbot-fuso
```

### 2. Buat virtual environment

```bash
python -m venv myenv

# Windows
myenv\Scripts\activate

# macOS / Linux
source myenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Buat file `.env`

Salin template dan isi API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_API_KEY=your_google_api_key_here
```

Dapatkan API key di: [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Ingest dokumen *(skip jika `chroma_db/` sudah ada)*

`chroma_db/` dan `bm25_chunks.json` sudah di-commit ke repo, jadi langkah ini
**hanya perlu dijalankan** jika ingin menambah atau mengubah file di `docs/`.

```bash
python ingest.py
```

Script ini akan:
- Load semua 13 file `.docx` dari `docs/`
- Chunk sesuai strategi (document-level untuk case report, section-based untuk SOP)
- Embed menggunakan `gemini-embedding-001`
- Simpan ke `chroma_db/` dan `bm25_chunks.json`

Setelah selesai, commit hasilnya:

```bash
git add chroma_db/ bm25_chunks.json
git commit -m "update: re-ingest knowledge base"
```

---

## Cara Menjalankan

### Jalankan aplikasi Streamlit

```bash
streamlit run app2.py
```

Buka browser di `http://localhost:8501`.

### Test modul secara individual

```bash
# Test retriever
python retriever.py

# Test LLM + RAG pipeline end-to-end
python llm.py

# Test monitoring (insert dummy data)
python monitoring.py
```

### Evaluasi offline (opsional)

Jalankan evaluasi RAG pipeline dengan LLM-as-judge terhadap 5 demo query:

```bash
python eval_offline.py
```

Output: ringkasan di terminal + `eval_results.csv`.

---

## Deployment ke Streamlit Community Cloud

1. Push repo ke GitHub (pastikan `chroma_db/` dan `bm25_chunks.json` ikut ter-commit)
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Pilih repo, branch `main`, file `app2.py`
4. Di **Advanced settings → Secrets**, tambahkan:

```toml
GOOGLE_API_KEY = "your_google_api_key_here"
```

5. Deploy — URL publik akan aktif dalam 1-2 menit

---

## Knowledge Base (13 file `.docx`)

### Explicit Knowledge — 4 file

| File | Isi | Model |
|---|---|---|
| `sop_canter_fe74hd.docx` | Service intervals, filter replacement, pre-trip checklist | Canter |
| `sop_fighter_x_fn61fsl.docx` | Service intervals, filter replacement, pre-trip checklist | Fighter X |
| `troubleshooting_canter_fe74hd.docx` | Overheating, starting failure, power loss, abnormal noise | Canter |
| `troubleshooting_fighter_x_fn61fsl.docx` | Overheating (incl. turbo), starting failure, power loss | Fighter X |

### Tacit Knowledge — 9 case report teknisi senior

| File | Kasus | Model |
|---|---|---|
| `case_01` | Cold start noise → timing chain tensioner | Canter |
| `case_02` | Hard starting → micro-crack pada fuel hose | Canter |
| `case_03` | Brake fade → teknik mengemudi (bukan kerusakan) | Canter |
| `case_04` | Overheat tanjakan → O-ring thermostat housing bergeser | Fighter X |
| `case_05` | Power loss bertahap → filter BBM sekunder tidak diganti | Fighter X |
| `case_06` | Vibrasi 65-70 km/h → balance weight propshaft lepas | Fighter X |
| `case_07` | Asap putih → coolant diganti air biasa | Fighter X |
| `case_08` | Keausan dini → intake hose retak bypass filter | Lintas model |
| `case_09` | Mesin mati mendadak → solar terkontaminasi air | Lintas model |

---
