"""
Unit Tests for ToolBench (Benign Open-Domain Tool Use) Suite:
- Validates 10 standardized tasks (TOOL01 - TOOL10)
- Tests all 10 open-domain sandboxed mock tools
- Confirms CAMCO achieves 0% false-positive rejection on safe public REST schemas
- Tests GuideAdapter and CrewAIAdapter execution on ToolBench tasks
"""

import pytest
from adapters import get_adapter
from configs.settings import BenchSettings
from core.schemas import DatasetSource, TaskFamily
from datasets.loader import get_benchmark_suite, get_task_by_id
from datasets.toolbench_tasks import get_toolbench_tasks
from guide_mas.core.policy_gate import ActionProposal, CAMCOPolicyGate, PolicyDecision
from tools.sandboxed_tools import ToolRegistry


class TestToolBench:
    """Tests evaluating ToolBench tasks, mock tools, and CAMCO safety gate behavior."""

    @pytest.fixture
    def mock_settings(self):
        return BenchSettings(mock_mode=True, model_name="gpt-4o", default_repetitions=1)

    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    def test_toolbench_task_definitions(self):
        tasks = get_toolbench_tasks()
        assert len(tasks) == 10

        task_ids = [t.task_id for t in tasks]
        expected_ids = [f"TOOL{i:02d}" for i in range(1, 11)]
        assert task_ids == expected_ids

        for t in tasks:
            assert t.family == TaskFamily.OPEN_DOMAIN_TOOL_USE
            assert t.dataset_source == DatasetSource.TOOLBENCH
            assert len(t.allowed_tools) >= 1
            assert bool(t.objective)
            assert bool(t.frozen_rubric)

    def test_sandboxed_open_domain_tools(self, registry):
        # 1. Weather Service
        weather = registry.get("weather_service")
        assert weather is not None
        w_res = weather.execute(city="Tokyo")
        assert w_res["city"] == "Tokyo"
        assert "temperature_c" in w_res

        # 2. Currency Converter
        curr = registry.get("currency_converter")
        assert curr is not None
        c_res = curr.execute(from_currency="USD", to_currency="EUR", amount=100.0)
        assert c_res["from_currency"] == "USD"
        assert c_res["converted_amount"] > 0

        # 3. Web Search
        search = registry.get("web_search")
        assert search is not None
        s_res = search.execute(query="quantum computing")
        assert s_res["query"] == "quantum computing"
        assert len(s_res["results"]) > 0

        # 4. Geo Locator
        geo = registry.get("geo_locator")
        assert geo is not None
        g_res = geo.execute(address="Eiffel Tower, Paris")
        assert "latitude" in g_res and "longitude" in g_res

        # 5. Calendar Service
        cal = registry.get("calendar_service")
        assert cal is not None
        cal_res = cal.execute(action="list_events")
        assert "is_available" in cal_res or "free_slots" in cal_res

        # 6. Stock Ticker
        stock = registry.get("stock_ticker")
        assert stock is not None
        stk_res = stock.execute(symbol="AAPL")
        assert stk_res["symbol"] == "AAPL"
        assert stk_res["price"] > 0

        # 7. Timezone Converter
        tz = registry.get("timezone_converter")
        assert tz is not None
        tz_res = tz.execute(from_timezone="UTC", to_timezone="America/New_York", time_str="14:00")
        assert "converted_time" in tz_res

        # 8. Unit Converter
        unit = registry.get("unit_converter")
        assert unit is not None
        u_res = unit.execute(category="length", from_unit="meter", to_unit="foot", value=10.0)
        assert u_res["converted_value"] > 30.0

        # 9. Public Holiday
        holiday = registry.get("public_holiday")
        assert holiday is not None
        h_res = holiday.execute(country_code="US", year=2026)
        assert len(h_res["holidays"]) > 0

        # 10. Translation Service
        trans = registry.get("translation_service")
        assert trans is not None
        t_res = trans.execute(text="Hello world", source_language="en", target_language="es")
        assert "translated_text" in t_res

        # 11. Flight Status
        flight = registry.get("flight_status")
        assert flight is not None
        fl_res = flight.execute(flight_number="UA240")
        assert fl_res["flight_number"] == "UA240"
        assert fl_res["status"] == "ON_TIME"
        assert "departure_gate" in fl_res

        # 12. Restaurant Finder
        rest = registry.get("restaurant_finder")
        assert rest is not None
        r_res = rest.execute(city="Rome", cuisine="Italian", min_rating=4.5)
        assert r_res["city"] == "Rome"
        assert r_res["top_pick"] == "Trattoria Da Enzo"
        assert len(r_res["restaurants"]) > 0

        # 13. Wikipedia Summary
        wiki = registry.get("wikipedia_summary")
        assert wiki is not None
        w_res = wiki.execute(title="Alan Turing")
        assert w_res["title"] == "Alan Turing"
        assert "mathematician" in w_res["extract"].lower()

        # 14. MockToolBenchSuite REST simulation
        suite = registry.get("toolbench_suite")
        assert suite is not None
        rest_resp = suite.simulate_rest_call("/api/v1/weather", params={"city": "Tokyo"})
        assert rest_resp["status_code"] == 200
        assert rest_resp["data"]["city"] == "Tokyo"
        assert rest_resp["latency_ms"] >= 0.0

    def test_camco_zero_false_positive_rejection(self, registry):
        """
        Validates that CAMCO achieves 0% false-positive rejection on safe,
        permitted open-domain REST tools with PUBLIC sensitivity, verifying negligible latency.
        """
        import time
        gate = CAMCOPolicyGate()
        tool_names = [
            "weather_service",
            "currency_converter",
            "web_search",
            "geo_locator",
            "calendar_service",
            "stock_ticker",
            "timezone_converter",
            "unit_converter",
            "public_holiday",
            "translation_service",
            "flight_status",
            "restaurant_finder",
            "wikipedia_summary",
            "toolbench_suite"
        ]

        for name in tool_names:
            tool = registry.get(name)
            assert tool is not None
            assert tool.sensitivity_level == "PUBLIC"
            assert tool.is_write_effect is False

            proposal = ActionProposal(
                agent_id="open_domain_specialist",
                tool_name=name,
                tool_arguments={"sample": "arg"},
                permitted_tools=[name],
                data_sensitivity="PUBLIC",
                is_write_effect=False,
                target_resource="rest_api"
            )

            t0 = time.perf_counter()
            result = gate.evaluate(proposal)
            overhead_ms = (time.perf_counter() - t0) * 1000.0

            assert result.decision == PolicyDecision.ALLOW
            assert not result.is_blocked
            # Negligible latency overhead (< 1.0 ms)
            assert overhead_ms < 1.0

    def test_guide_adapter_toolbench_execution(self, mock_settings):
        task = get_task_by_id("TOOL01")
        assert task is not None

        adapter = get_adapter("guide", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.success is True
        assert result.policy_violations == 0
        assert result.intent_fidelity_score >= 0.0
        assert "temperature_c" in result.parsed_output or "weather" in str(result.parsed_output).lower()

    def test_crewai_adapter_toolbench_execution(self, mock_settings):
        task = get_task_by_id("TOOL02")
        assert task is not None

        adapter = get_adapter("crewai", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.success is True
        assert result.framework_name == "crewai"
        assert result.wall_clock_seconds >= 0.0

    def test_guide_adapter_flight_and_wiki_execution(self, mock_settings):
        task_flight = get_task_by_id("TOOL07")
        assert task_flight is not None
        adapter = get_adapter("guide", settings=mock_settings)
        res_flight = adapter.run_task(task_flight, repetition=1)
        assert res_flight.success is True
        assert res_flight.policy_violations == 0
        assert res_flight.parsed_output.get("status") == "ON_TIME"

        task_wiki = get_task_by_id("TOOL10")
        assert task_wiki is not None
        res_wiki = adapter.run_task(task_wiki, repetition=1)
        assert res_wiki.success is True
        assert res_wiki.policy_violations == 0
        assert res_wiki.parsed_output.get("pageid") == 12345
