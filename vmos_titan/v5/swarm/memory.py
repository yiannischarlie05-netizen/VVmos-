try:
    import redis
except ImportError:
    redis = None
import sqlite3
import json

class SwarmMemory:
    """
    Manages the distributed state for the agent swarm using Redis for
    low-latency messaging and SQLite for persistent storage.
    """
    def __init__(self, redis_host='localhost', redis_port=6379, db_path='swarm_memory.db'):
        if redis is not None:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
        else:
            self.redis_client = None
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database and creates the state table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_state (
                    agent_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def update_state(self, agent_id: str, state: dict):
        """Updates the state of an agent in both Redis and SQLite."""
        state_json = json.dumps(state)
        # Update Redis for fast access
        if self.redis_client:
            self.redis_client.set(f"agent:{agent_id}", state_json)
        # Update SQLite for persistence
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO agent_state (agent_id, state)
                VALUES (?, ?)
            ''', (agent_id, state_json))
            conn.commit()

    def get_state(self, agent_id: str) -> dict:
        """Retrieves the state of an agent, checking Redis first, then SQLite."""
        if self.redis_client:
            state_json = self.redis_client.get(f"agent:{agent_id}")
            if state_json:
                return json.loads(state_json)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT state FROM agent_state WHERE agent_id = ?', (agent_id,))
            row = cursor.fetchone()
            if row:
                # Cache in Redis for future requests
                if self.redis_client:
                    self.redis_client.set(f"agent:{agent_id}", row[0])
                return json.loads(row[0])
        return None

    def publish_message(self, channel: str, message: dict):
        """Publishes a message to a Redis channel for inter-agent communication."""
        if self.redis_client:
            self.redis_client.publish(channel, json.dumps(message))

    def subscribe(self, channel: str):
        """Subscribes to a Redis channel to receive messages."""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        return None

if __name__ == '__main__':
    # Example Usage
    memory = SwarmMemory(db_path='test_swarm.db')
    
    # Update state for two agents
    memory.update_state('strategic_queen_1', {'objective': 'breach_firewall', 'status': 'decomposing'})
    memory.update_state('recon_worker_5', {'target': '10.0.0.1', 'status': 'scanning'})

    # Retrieve state
    sq1_state = memory.get_state('strategic_queen_1')
    print(f"StrategicQueen1 State: {sq1_state}")

    # Publish a message
    memory.publish_message('swarm_intel', {'type': 'vulnerability', 'target': '10.0.0.1', 'port': 443})
    print("Published vulnerability intel.")
