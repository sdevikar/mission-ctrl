from pathlib import Path

import pytest
from mission_ctrl_core.models import Bucket, SpecStatus
from mission_ctrl_core.stores import IntentStore

FIXTURES = Path(__file__).parent / "fixtures"
NAMES = ["empty-project", "mid-flight", "complex-graph"]


@pytest.fixture(params=NAMES)
def store(request: pytest.FixtureRequest) -> IntentStore:
    return IntentStore(FIXTURES / request.param)


def test_fixture_validates_clean(store: IntentStore) -> None:
    assert store.validate_all() == []
    assert len(store.meta.read_all()) >= 1


def test_fixture_ids_are_unique(store: IntentStore) -> None:
    ids = [e.event_id for e in store.meta.read_all()]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)  # append-only log is id-sorted


def test_empty_project_has_no_specs_or_backlog() -> None:
    store = IntentStore(FIXTURES / "empty-project")
    assert store.specs.read().nodes == []
    assert store.backlog.read().items == []
    got = store.get_current_intent()
    assert got.spec_count == 0
    assert got.current_spec is None


def test_mid_flight_current_and_next() -> None:
    store = IntentStore(FIXTURES / "mid-flight")
    got = store.get_current_intent()
    assert got.current_spec == "spec_001"  # the only in_progress spec
    assert got.next_specs == []  # spec_002 is draft, not design_approved
    assert store.specs.get("spec_002").status is SpecStatus.DRAFT
    assert [i.id for i in store.backlog.search(bucket=Bucket.MVP_CRITICAL)] == [
        "idea_002"
    ]


def test_complex_graph_chain_structure() -> None:
    store = IntentStore(FIXTURES / "complex-graph")
    nodes = store.specs.read().nodes
    by_id = {n.id: n for n in nodes}
    # multiple dependency chains, a blocked spec, and done specs
    assert by_id["spec_001"].status is SpecStatus.DONE
    assert by_id["spec_002"].status is SpecStatus.DONE
    assert by_id["spec_004"].status is SpecStatus.BLOCKED
    assert set(by_id["spec_004"].depends_on) == {"spec_002", "spec_005"}
    # cycle-free
    store.specs.validate_no_cycles()
    got = store.get_current_intent()
    assert got.current_spec is None  # nothing in_progress
    # only spec_003 is design_approved; spec_002 is done so it is ready
    assert got.next_specs == ["spec_003"]


def test_fixture_event_payload_round_trips() -> None:
    store = IntentStore(FIXTURES / "mid-flight")
    events = store.meta.read_all()
    types = [e.event_type for e in events]
    assert "INTENT_CREATED" in types
    assert "SPEC_CREATED" in types
    assert "SPEC_STATUS_UPDATED" in types
