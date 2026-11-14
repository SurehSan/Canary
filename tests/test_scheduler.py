"""CAN-REQ-003/004/009: one scheduler cycle collects (when due), sends P1/P2 queue, and runs digest (when due)."""
from canary.scheduler import run_cycle
from tests.conftest import org_id


def test_cycle_collects_and_processes_queue_when_due(app, db):
    summary = run_cycle(db, collect=True, digest=False)
    assert summary["touched"] == 1
    fern = org_id(db, "Fernwood Labs")
    assert db.execute("SELECT COUNT(*) FROM alerts WHERE org_id=?", (fern,)).fetchone()[0] == 1
    # No SMTP in the hermetic config: the queued P2 is processed and recorded as rejected/blocked, never sent.
    statuses = [r[0] for r in db.execute("SELECT status FROM notifications")]
    assert statuses and "pending" not in statuses and "sent" not in statuses
    runs = db.execute("SELECT DISTINCT trigger FROM collection_runs").fetchall()
    assert [r[0] for r in runs] == ["scheduled"]


def test_cycle_without_collection_does_not_collect(app, db):
    run_cycle(db, collect=False, digest=False)
    assert db.execute("SELECT COUNT(*) FROM collection_runs").fetchone()[0] == 0
