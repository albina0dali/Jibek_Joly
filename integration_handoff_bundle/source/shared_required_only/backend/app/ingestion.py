from collections import deque


class IngestionPipeline:
    def __init__(self):
        self.seen = set()
        self.order = deque(maxlen=10000)
        self.last = {}
        self.speeds = {}
        self.metrics = dict(accepted=0, duplicates=0, invalid=0, stale=0, out_of_order=0)

    def ingest(self, event, now):
        if not {'id', 'train_id', 'timestamp', 'speed_kmh'} <= event.keys() or not 0 <= event['speed_kmh'] <= 160:
            self.metrics['invalid'] += 1
            return None
        if event['id'] in self.seen:
            self.metrics['duplicates'] += 1
            return None
        if now - event['timestamp'] > 10:
            self.metrics['stale'] += 1
            return None
        if event['timestamp'] < self.last.get(event['train_id'], -1):
            self.metrics['out_of_order'] += 1
            return None
        if len(self.order) == self.order.maxlen:
            self.seen.discard(self.order[0])
        self.order.append(event['id'])
        self.seen.add(event['id'])
        train_id = event['train_id']
        self.last[train_id] = event['timestamp']
        speed = .7 * self.speeds.get(train_id, event['speed_kmh']) + .3 * event['speed_kmh']
        self.speeds[train_id] = speed
        self.metrics['accepted'] += 1
        return {**event, 'speed_kmh': round(speed, 1)}


class EventBus:
    """In-process synchronous subscribers; adapter boundary for a future broker."""
    def __init__(self):
        self.handlers = []
        self.events_processed = 0

    def subscribe(self, handler):
        self.handlers.append(handler)

    def publish(self, event):
        self.events_processed += 1
        for handler in self.handlers:
            handler(event)
