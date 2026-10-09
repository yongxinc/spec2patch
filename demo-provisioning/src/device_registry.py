"""裝置註冊表與狀態機。"""

PENDING = "pending"
PROVISIONED = "provisioned"
PROVISION_FAILED = "provision_failed"
REVOKED = "revoked"

ALLOWED_TRANSITIONS = {
    PENDING: {PROVISIONED, PROVISION_FAILED, REVOKED},
    PROVISIONED: {REVOKED},
    PROVISION_FAILED: {PENDING},
    REVOKED: {PENDING},
}


class DuplicateDeviceError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


class DeviceRegistry:
    def __init__(self):
        self._devices = {}

    def register(self, mac):
        if mac in self._devices:
            raise DuplicateDeviceError(mac)
        self._devices[mac] = PENDING

    def get_state(self, mac):
        return self._devices.get(mac)

    def transition(self, mac, new_state):
        current = self._devices[mac]
        if new_state not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(f"{current} -> {new_state}")
        self._devices[mac] = new_state
