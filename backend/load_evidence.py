"""Load web-verified evidence data into the portfolio_evidence table.

Reads from frontend/public/portfolio_evidence.json and syncs to production DB.
Run: cd backend && source .env && python load_evidence.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from models.company import Base, PortfolioEvidence

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set. Run: source .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine, tables=[PortfolioEvidence.__table__])

# Load evidence from the static JSON (single source of truth)
json_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
with open(json_path) as f:
    EVIDENCE = json.load(f)

# Map company names → company IDs from the database
with Session(engine) as session:
    rows = session.execute(text("SELECT id, name FROM companies WHERE is_portfolio = true")).fetchall()
    name_to_id = {row[1]: row[0] for row in rows}

    # Clear existing evidence
    session.execute(text("DELETE FROM portfolio_evidence"))

    loaded = 0
    for company_name, data in EVIDENCE.items():
        cid = name_to_id.get(company_name)
        if not cid:
            print(f"  ⚠ No company_id for '{company_name}' — skipping")
            continue

        # Map frontend field names back to DB column names
        ev = PortfolioEvidence(
            company_id=cid,
            executives=data.get("executives", []),
            customers=data.get("named_customers", []),
            ai_initiatives=data.get("ai_initiatives", []),
            tech_stack=data.get("tech_stack", []),
            github=data.get("github", {}),
            careers=data.get("careers", {}),
            talent=data.get("talent", {}),
            news=data.get("recent_news", []),
            evidence=data.get("key_evidence", []),
            narrative=data.get("narrative_summary", ""),
        )
        session.add(ev)
        ev_count = len(data.get("key_evidence", []))
        cust_count = len(data.get("named_customers", []))
        ai_count = len(data.get("ai_initiatives", []))
        tech_count = len(data.get("tech_stack", []))
        print(f"  ✓ {company_name} ({ev_count} evidence, {cust_count} customers, {ai_count} AI initiatives, {tech_count} tech)")
        loaded += 1

    session.commit()
    print(f"\n✓ Loaded evidence for {loaded}/{len(EVIDENCE)} companies")
