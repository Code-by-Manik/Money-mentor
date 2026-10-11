<div align="center">

# 💸 Money Mentor

### Stop just *storing* your transactions. Start *understanding* your money.

A personal finance tracker that turns messy bank statements into clear, trustworthy insight.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/status-MVP%20foundation-orange?style=for-the-badge)

</div>

---

## ✨ What is Money Mentor?

Money Mentor takes your bank statement CSVs, cleans them up, stores them safely, and shows you where your money actually goes. It is built with a simple rule: **a pretty chart is worthless if the numbers behind it are wrong.**

> 🚧 **Honest status:** Money Mentor is a working MVP foundation, not a production-ready app. The roadmap below clearly separates what is built from what is planned.

---

## ✅ What works today

| Feature | Details |
|---|---|
| ⚡ **FastAPI backend** | REST API with interactive Swagger docs |
| 🗄️ **SQLite persistence** | SQLAlchemy models for accounts and statement records |
| 📥 **CSV importing** | Dates, descriptions, money in/out and balances |
| 🧹 **Smart normalization** | Multiple date formats, blank descriptions, missing balances |
| 🚫 **Duplicate prevention** | Re-importing the same statement won't double your transactions |
| 🛡️ **Bad-data defense** | Skips repeated headers and summary rows, rejects malformed amounts and reports them |
| 📊 **Basic dashboard** | Income, expenses, net cash flow, transaction counts, category totals |
| 🧪 **Edge-case tests** | Dedicated test script, kept separate from the main dataset |

---

## 🔭 Roadmap

Planned work, not yet implemented:

**Phase 1: Stabilize the foundation** *(partially complete)*
Audit endpoints, verify relationships, strengthen import handling, add regression tests.

**Phase 2: Analytics v1** *(next milestone)*
- Overview: income, expenses, net cash flow, savings rate, change vs. previous period
- Spending analysis: category totals, share of expenses, top categories
- Trends: monthly income vs. expenses, period comparisons
- Account-wise and consolidated views, with **internal transfers never double-counted**
- Monthly views and custom date ranges

**Phase 3: Manageable transactions**
Search, filters, edit, recategorize, safe delete, better import review.

**Phase 4: Financial planning**
Budgets, spending limits, savings goals, recurring payment detection, insights and alerts.

**Phase 5: Everyday-ready**
Backup and restore, security review, broader testing, deployment prep, UI polish.

---

## 🧱 Project structure

```
Money-mentor/
├── main.py                 # FastAPI app and endpoints
├── models.py               # SQLAlchemy models
├── database.py             # DB engine and session management
├── importers/
│   └── csv_parser.py       # CSV parsing and normalization
├── frontend/
│   ├── index.html          # Dashboard structure
│   ├── style.css           # Styling
│   └── script.js           # Fetches and renders data
└── test_edge_cases.py      # Import edge-case tests
```

---

## 🚀 Getting started

```bash
# 1. Clone
git clone https://github.com/Code-by-Manik/Money-mentor.git
cd Money-mentor

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn sqlalchemy python-multipart

# 4. Run the backend
uvicorn main:app --reload
```

Then open:

- **API docs (Swagger):** http://127.0.0.1:8000/docs
- **Frontend:** open `frontend/index.html` in your browser

> The local SQLite database and `.venv` are intentionally excluded from the repo, so your first run starts with a fresh database.

### Run the edge-case tests

```bash
python test_edge_cases.py
```

---

## 🧭 Design principles

1. **Inspect first, change second.** No blind rewrites.
2. **Small, focused changes.** Each one tested before the next.
3. **Your data is sacred.** No resets, no lost history.
4. **One source of truth.** Financial calculations live in reusable backend services, not scattered across endpoints and frontend code.
5. **Numbers over visuals.** Correctness first, charts second.
6. **Commit working milestones.**

---

## 🤝 Contributing

This is an early-stage personal project. Issues and ideas are welcome. Please open an issue before sending a large pull request.

---

<div align="center">

**Built by [Manik](https://github.com/Code-by-Manik)** 

*Know your money. Own your future.*

</div>
