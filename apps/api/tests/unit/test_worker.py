from arutech_api.worker import celery_app, ping


def test_ping_task_is_registered() -> None:
    assert "arutech.ping" in celery_app.tasks


def test_ping_executes_synchronously_via_apply() -> None:
    # `.apply()` runs the task body locally without a broker/worker, which is
    # exactly what we want to unit test the task logic in isolation.
    result = ping.apply()
    assert result.successful()
    assert result.result == "pong"
