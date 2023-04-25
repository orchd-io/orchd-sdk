class LamportClock:
    def __init__(self):
        self._clock = 0

    def get_clock(self):
        return self._clock

    def tick(self):
        self._clock += 1

    def sync(self, clock):
        self._clock = max(self._clock, clock) + 1


class VectorClock:
    def __init__(self, size):
        self._clock = [0] * size

    def get_clock(self):
        return self._clock

    def tick(self, index):
        self._clock[index] += 1

    def sync(self, clock):
        for i in range(len(self._clock)):
            self._clock[i] = max(self._clock[i], clock[i])


def synced_emit():
    def wrapper(self, event, clock):
        clock.tick()
        response = self.communicator.emit_event(event, self.clock)
        clock.sync(response.clock)
        return response
    return wrapper
