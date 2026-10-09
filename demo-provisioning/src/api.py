"""最小化的查詢 API(不依賴框架)。"""


def get_device(registry, mac):
    state = registry.get_state(mac)
    if state is None:
        return 404, {"error": "device not found"}
    return 200, {"mac": mac, "state": state}
