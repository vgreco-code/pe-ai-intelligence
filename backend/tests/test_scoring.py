"""Tests for portfolio, training, and benchmark API endpoints.
Replaces old scoring_service tests — now testing the Postgres-backed API layer."""
import pytest


# ─── Portfolio Scores ────────────────────────────────────────────

class TestPortfolioScores:
    def test_returns_only_portfolio_companies(self, seeded_client):
        resp = seeded_client.get("/api/portfolio_scores")
        assert resp.status_code == 200
        data = resp.json()
        names = [c["name"] for c in data]
        assert "Cairn Applications" in names
        assert "SMRTR" in names
        assert "AutoTime" in names
        # Training-only company should NOT appear
        assert "Salesforce" not in names

    def test_portfolio_count(self, seeded_client):
        data = seeded_client.get("/api/portfolio_scores").json()
        assert len(data) == 3

    def test_portfolio_company_shape(self, seeded_client):
        data = seeded_client.get("/api/portfolio_scores").json()
        company = next(c for c in data if c["name"] == "Cairn Applications")
        required_keys = {"name", "vertical", "employee_count", "description",
                         "website", "founded_year", "composite_score", "tier",
                         "wave", "pillar_scores", "category_scores"}
        assert required_keys.issubset(set(company.keys()))

    def test_portfolio_scores_values(self, seeded_client):
        data = seeded_client.get("/api/portfolio_scores").json()
        cairn = next(c for c in data if c["name"] == "Cairn Applications")
        assert cairn["composite_score"] == 3.30
        assert cairn["tier"] == "AI-Buildable"
        assert cairn["wave"] == 1
        assert cairn["vertical"] == "Waste Hauling SaaS"

    def test_portfolio_pillar_scores_present(self, seeded_client):
        data = seeded_client.get("/api/portfolio_scores").json()
        cairn = next(c for c in data if c["name"] == "Cairn Applications")
        ps = cairn["pillar_scores"]
        assert isinstance(ps, dict)
        assert len(ps) == 17
        assert ps["data_quality"] == 3.6
        assert ps["ai_momentum"] == 3.3

    def test_portfolio_category_scores_present(self, seeded_client):
        data = seeded_client.get("/api/portfolio_scores").json()
        cairn = next(c for c in data if c["name"] == "Cairn Applications")
        cs = cairn["category_scores"]
        assert "Data & Analytics" in cs
        assert cs["Data & Analytics"] == 3.5

    def test_empty_portfolio(self, client):
        """No companies in DB → empty list"""
        data = client.get("/api/portfolio_scores").json()
        assert data == []


# ─── Competitive Benchmarks ──────────────────────────────────────

class TestCompetitiveBenchmarks:
    def test_returns_portfolio_benchmarks_key(self, seeded_client):
        resp = seeded_client.get("/api/competitive_benchmarks")
        assert resp.status_code == 200
        data = resp.json()
        assert "portfolio_benchmarks" in data

    def test_benchmark_count(self, seeded_client):
        data = seeded_client.get("/api/competitive_benchmarks").json()
        assert len(data["portfolio_benchmarks"]) == 1  # Only Cairn has a benchmark

    def test_benchmark_shape(self, seeded_client):
        data = seeded_client.get("/api/competitive_benchmarks").json()
        bm = data["portfolio_benchmarks"][0]
        required = {"name", "score", "tier", "wave", "peer_verticals", "peer_count",
                     "vertical_rank", "vertical_percentile", "vertical_avg",
                     "vertical_max", "vertical_min", "nearest_peers"}
        assert required.issubset(set(bm.keys()))

    def test_benchmark_values(self, seeded_client):
        data = seeded_client.get("/api/competitive_benchmarks").json()
        bm = data["portfolio_benchmarks"][0]
        assert bm["name"] == "Cairn Applications"
        assert bm["vertical_percentile"] == 76.0
        assert bm["peer_count"] == 25
        assert bm["vertical_rank"] == 6

    def test_benchmark_nearest_peers(self, seeded_client):
        data = seeded_client.get("/api/competitive_benchmarks").json()
        bm = data["portfolio_benchmarks"][0]
        assert len(bm["nearest_peers"]) == 1
        assert bm["nearest_peers"][0]["name"] == "PeerCo"

    def test_empty_benchmarks(self, client):
        data = client.get("/api/competitive_benchmarks").json()
        assert data["portfolio_benchmarks"] == []


# ─── Wave Sequencing ─────────────────────────────────────────────

class TestWaveSequencing:
    def test_wave_keys(self, seeded_client):
        data = seeded_client.get("/api/wave_sequencing").json()
        assert "Wave 1 (Q1-Q2)" in data
        assert "Wave 2 (Q3-Q4)" in data
        assert "Wave 3 (Year 2)" in data

    def test_wave_assignment(self, seeded_client):
        data = seeded_client.get("/api/wave_sequencing").json()
        w1_names = [c["name"] for c in data["Wave 1 (Q1-Q2)"]]
        w3_names = [c["name"] for c in data["Wave 3 (Year 2)"]]
        assert "Cairn Applications" in w1_names
        assert "SMRTR" in w1_names
        assert "AutoTime" in w3_names

    def test_wave_entry_shape(self, seeded_client):
        data = seeded_client.get("/api/wave_sequencing").json()
        entry = data["Wave 1 (Q1-Q2)"][0]
        assert "name" in entry
        assert "score" in entry
        assert "tier" in entry
        assert "top_category" in entry


# ─── Tier Distribution ───────────────────────────────────────────

class TestTierDistribution:
    def test_tier_counts(self, seeded_client):
        data = seeded_client.get("/api/tier_distribution").json()
        assert data.get("AI-Buildable", 0) == 2
        assert data.get("AI-Limited", 0) == 1

    def test_empty_distribution(self, client):
        data = client.get("/api/tier_distribution").json()
        assert data == {}


# ─── Model Metrics ───────────────────────────────────────────────

class TestModelMetrics:
    def test_returns_model_data(self, seeded_client):
        resp = seeded_client.get("/api/model_metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version"] == "4.1"
        assert data["framework"] == "XGBoost"
        assert data["num_dimensions"] == 17

    def test_model_accuracy_values(self, seeded_client):
        data = seeded_client.get("/api/model_metrics").json()
        assert data["cv_accuracy"] == 0.8932
        assert data["cv_folds"] == 5
        assert data["backtest_count"] == 58

    def test_feature_importance_present(self, seeded_client):
        data = seeded_client.get("/api/model_metrics").json()
        fi = data["feature_importance"]
        assert isinstance(fi, dict)
        assert "data_quality" in fi
        assert "ai_engineering" in fi

    def test_backtest_results_present(self, seeded_client):
        data = seeded_client.get("/api/model_metrics").json()
        bt = data["backtest_results"]
        assert isinstance(bt, list)
        assert len(bt) == 1
        assert bt[0]["name"] == "TestCo"
        assert bt[0]["correct"] is True

    def test_categories_and_labels(self, seeded_client):
        data = seeded_client.get("/api/model_metrics").json()
        assert "Data & Analytics" in data["categories"]
        assert data["dimension_labels"]["data_quality"] == "Data Quality"

    def test_empty_metrics(self, client):
        data = client.get("/api/model_metrics").json()
        assert data == {}


# ─── Training Stats ──────────────────────────────────────────────

class TestTrainingStats:
    def test_total_companies(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        assert data["total_companies"] == 4  # 3 portfolio + 1 training

    def test_dimension_count(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        # Only Cairn has individual dimension_scores rows
        assert data["num_dimensions"] == 17

    def test_tier_distribution(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        td = data["tier_distribution"]
        assert isinstance(td, dict)
        assert td.get("AI-Buildable", 0) == 2
        assert td.get("AI-Limited", 0) == 1
        assert td.get("AI-Ready", 0) == 1

    def test_avg_score(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        # (3.30 + 3.15 + 2.10 + 4.50) / 4 = 3.2625
        assert 3.0 < data["avg_score"] < 3.5

    def test_top_companies(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        top = data["top_companies"]
        assert len(top) <= 10
        # Should be sorted desc by score
        assert top[0]["name"] == "Salesforce"
        assert top[0]["composite_score"] == 4.50

    def test_dimension_stats_shape(self, seeded_client):
        data = seeded_client.get("/api/training_stats").json()
        ds = data["dimension_stats"]
        assert isinstance(ds, dict)
        if "data_quality" in ds:
            stat = ds["data_quality"]
            assert "mean" in stat
            assert "std" in stat
            assert "min" in stat
            assert "max" in stat
            assert "label" in stat


# ─── Training Set ────────────────────────────────────────────────

class TestTrainingSet:
    def test_returns_all_companies(self, seeded_client):
        data = seeded_client.get("/api/large_training_set").json()
        assert len(data) == 4  # All companies, portfolio + training

    def test_training_entry_has_pillars(self, seeded_client):
        data = seeded_client.get("/api/large_training_set").json()
        cairn = next(c for c in data if c["name"] == "Cairn Applications")
        assert "pillars" in cairn
        assert isinstance(cairn["pillars"], dict)

    def test_training_entry_has_signals(self, seeded_client):
        data = seeded_client.get("/api/large_training_set").json()
        sf = next(c for c in data if c["name"] == "Salesforce")
        assert sf["text_chars"] == 15000
        assert sf["ai_hiring_signals"] == 8

    def test_training_entry_has_metadata(self, seeded_client):
        data = seeded_client.get("/api/large_training_set").json()
        sf = next(c for c in data if c["name"] == "Salesforce")
        assert sf["is_public"] is True
        assert sf["has_ai_features"] is True
        assert sf["cloud_native"] is True
        assert sf["api_ecosystem_strength"] == 4.5


# ─── Database Model Tests ────────────────────────────────────────

class TestModels:
    def test_company_id_auto_generated(self, db):
        from models.company import Company
        c = Company(name="TestCo Auto ID")
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.id.startswith("co_")
        assert len(c.id) == 11  # "co_" + 8 hex chars

    def test_company_portfolio_flag(self, db):
        from models.company import Company
        c = Company(name="Portfolio Co", is_portfolio=True)
        db.add(c)
        db.commit()
        result = db.query(Company).filter(Company.is_portfolio == True).all()
        assert len(result) == 1
        assert result[0].name == "Portfolio Co"

    def test_dimension_score_creation(self, db):
        from models.company import Company, DimensionScore
        c = Company(name="DimTest Co")
        db.add(c)
        db.flush()
        ds = DimensionScore(company_id=c.id, dimension="data_quality", score=3.5)
        db.add(ds)
        db.commit()
        result = db.query(DimensionScore).filter(DimensionScore.company_id == c.id).all()
        assert len(result) == 1
        assert result[0].score == 3.5

    def test_company_score_json_fields(self, db):
        from models.company import Company, CompanyScore
        c = Company(name="JSONTest Co")
        db.add(c)
        db.flush()
        ps = {"data_quality": 3.0, "ai_engineering": 4.0}
        cs = CompanyScore(company_id=c.id, composite_score=3.5, tier="AI-Buildable", pillar_scores=ps)
        db.add(cs)
        db.commit()
        result = db.query(CompanyScore).filter(CompanyScore.company_id == c.id).first()
        assert result.pillar_scores["data_quality"] == 3.0
        assert result.pillar_scores["ai_engineering"] == 4.0
