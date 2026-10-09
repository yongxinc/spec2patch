import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import provisioning
from device_registry import DeviceRegistry, PROVISIONED, PROVISION_FAILED


def test_success(monkeypatch):
    monkeypatch.setattr(provisioning.time, "sleep", lambda s: None)
    r = DeviceRegistry(); r.register("aa")
    assert provisioning.provision(r, "aa", lambda m: True)
    assert r.get_state("aa") == PROVISIONED


def test_retry_then_fail(monkeypatch):
    sleeps, calls = [], []
    monkeypatch.setattr(provisioning.time, "sleep", sleeps.append)
    r = DeviceRegistry(); r.register("aa")
    assert not provisioning.provision(r, "aa", lambda m: calls.append(m) or False)
    assert len(calls) == 4  # 首次 + 3 次重試
    assert sleeps == [1, 2, 4]
    assert r.get_state("aa") == PROVISION_FAILED
