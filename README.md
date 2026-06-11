# Olist Customer Churn — Analytics Project

End-to-end customer analytics for the public [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).  
Cleans raw CSV data, exports to PostgreSQL, then provides an interactive Streamlit dashboard for customer retention, churn, lifetime value, and satisfaction metrics.

---

## Dataset

The dataset contains ~100k orders made at Olist (a Brazilian marketplace) between 2016 and 2018 across 27 states.

| Table | Rows | Description |
|---|---|---|
| `customers` | 99,441 | Customer ID, unique ID, zip code, city, state |
| `geolocation` | 738k (deduped) | Zip-code-prefix lat/lng coordinates |
| `orders` | 99,441 | Order status, purchase/approval/delivery timestamps |
| `order_items` | 112,650 | Line items: product, seller, price, freight |
| `order_payments` | 103,886 | Payment type, installments, value |
| `order_reviews` | 98,410 | Review score (1–5), comments, timestamps |
| `products` | 32,951 | Category, name/description length, weight, dimensions |
| `sellers` | 3,095 | Seller location info |
| `product_category_translation` | 71 | Portuguese → English category names |

---

## Project Structure

```
├── src/                    # Reusable Python modules
│   ├── config.py           # Environment-based configuration
│   └── database.py         # Engine, query runner, data loaders
├── dashboard/              # Streamlit dashboard
│   ├── app.py              # Entry point — run with `streamlit run`
│   ├── kpi_cards.py        # KPI metric computations
│   └── charts.py           # Plotly chart query & rendering
├── notebooks/
│   └── EDA.ipynb           # Data cleaning pipeline
├── sql/
│   └── analysis.sql        # SQL analysis queries
├── raw_data/               # Original CSV files (unchanged)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 16+ running locally

### Installation

```bash
# 1. Clone / navigate to the project
cd olist-customer-churn

# 2. Create a virtual environment (optional but recommended)
python3 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the database URL
cp .env.example .env
# Edit .env:  OLIST_DB_URL=postgresql://user:password@localhost:5432/olist
```

### Database Setup

```bash
# 1. Create the database
createdb olist

# 2. Run the EDA notebook to clean CSVs and export to PostgreSQL
#    Open notebooks/EDA.ipynb in Jupyter and run all cells.
#    This loads raw CSVs, handles missing values & duplicates, and
#    calls df.to_sql() to populate 9 tables.

# 3. (Optional) Run analysis queries
psql -d olist -f sql/analysis.sql
```

### Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at **http://localhost:8501**.

---

## Data Cleaning Pipeline

The notebook `notebooks/EDA.ipynb` performs the following steps:

### Missing Values

| Table | Handling |
|---|---|
| `customers` | No missing values |
| `geolocation` | No missing values |
| `orders` | Missing timestamps (`order_approved_at`, `order_delivered_*`) kept as `NULL` — genuinely not yet processed |
| `order_items` | No missing values |
| `order_payments` | No missing values |
| `order_reviews` | Empty comments → `''`; rows missing `review_score` or `order_id` → dropped; missing timestamps → `'unknown'` |
| `products` | Missing `product_category_name` (610) → `'unknown'`; missing weight/dimensions (2) → median |
| `sellers` | No missing values |
| `category_translation` | No missing values |

### Duplicates

| Table | Handling |
|---|---|
| `geolocation` | 261,831 full-row duplicates → dropped |
| `order_reviews` | 789 duplicate `review_id` → keep first |
| `customers` | 3,345 duplicate `customer_unique_id` → **kept** (legitimate repeat customers) |

### Dropped Columns

Products table: `product_name_lenght`, `product_description_lenght`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`

---

## Metrics & Formulas

### 1. Customer Retention Rate (CRR)

```
CRR = (Customers active in Year Y who also ordered in Year Y+1)
      / (Customers active in Year Y) × 100
```

Measures what % of customers return the following year. Computed year-over-year.

### 2. Repeat Purchase Rate (RPR)

```
RPR = (Customers with more than 1 order) / (Total customers) × 100
```

What % of unique customers placed more than one order.

### 3. Customer Churn Rate

```
Churn = (Customers whose last order is before the final year in data)
       / (Total customers in that cohort) × 100
```

Broken down by the year of their last order.

### 4. Customer Lifetime Value (LTV / CLTV)

```
LTV = Average total revenue per unique customer
```

Also shown as components:
- **Average Order Value** = total revenue / total orders
- **Avg Purchases per Customer**
- **Avg Lifespan** (years between first and last order)

### 5. Customer Satisfaction Score (CSAT)

```
CSAT = (Reviews with score ≥ 4) / (Total reviews) × 100
```

Based on the 1–5 review score scale.

### 6. Net Promoter Score (NPS)

```
NPS = % Promoters (score 5) − % Detractors (scores 1–3)
```

Adapted from the standard 0–10 scale to the 1–5 scale available in the data:
- Promoters = 5
- Passives = 4
- Detractors = 1–3

### 7. Customer Effort Score (CES)

Not calculable — the Olist dataset does not include effort survey data.

---

## Dashboard Features

| Section | Content |
|---|---|
| **Sidebar filters** | Year range slider, multi-select states and product categories |
| **KPI row** | CRR, RPR, Churn, Avg LTV, CSAT, NPS — all respond to filters |
| **Chart row 1** | Top 10 states by revenue (bar) + Revenue trend over years (line) |
| **Chart row 2** | Customers acquired per month (bar) + Best month each year (bar) |
| **Chart row 3** | Top 10 product categories by revenue (horizontal bar) + Review score distribution (bar) |
| **Expandable tables** | CRR by year, monthly revenue, payment type distribution, delivery performance, top 3 states × top 3 categories |

---

## SQL Analysis

`sql/analysis.sql` contains standalone queries for:

- Top 3 states by sales and revenue
- Top 3 states with their top 3 product categories
- Monthly customer acquisition
- Most profitable month per year
- CRR, RPR, Churn, LTV, CSAT, NPS (same formulas as the dashboard)

Run with:

```bash
psql -d olist -f sql/analysis.sql
```

---

## Tech Stack

| Component | Tool |
|---|---|
| Language | Python 3.9 |
| Data processing | pandas, numpy |
| Database | PostgreSQL 16 |
| SQL toolkit | SQLAlchemy 2.0 |
| Visualization | Plotly, Streamlit |
| Data cleaning | Jupyter Notebook |
