"""
Verifying:
- Discovery: nodes find each other over multicast
- Messaging: broadcast and direct send
"""

import asyncio
import time
import unittest
from typing import List, Dict, Any

from p2p.p2p_node import P2PNode


class P2PTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.messages_a: List[Dict[str, Any]] = []
        self.messages_b: List[Dict[str, Any]] = []

        self.node_a = P2PNode("veh-A", listen_host="127.0.0.1", listen_port=0, announce_interval=0.3, peer_timeout=1.5)
        self.node_b = P2PNode("veh-B", listen_host="127.0.0.1", listen_port=0, announce_interval=0.3, peer_timeout=1.5)

        self.node_a.on_message(lambda m: self.messages_a.append(m))
        self.node_b.on_message(lambda m: self.messages_b.append(m))

        await self.node_a.start()
        await self.node_b.start()

        # wait for discovery
        t0 = time.time()
        while ("veh-A" not in self.node_b.peers or "veh-B" not in self.node_a.peers) and time.time() - t0 < 5.0:
            await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        await self.node_a.stop()
        await self.node_b.stop()

    async def test_discovery_and_broadcast(self):
        await self.node_a.broadcast({"type": "location_update", "payload": {"x": 1}})
        await asyncio.sleep(0.5)
        self.assertTrue(any(m.get('type') == 'location_update' for m in self.messages_b))

    async def test_send_to(self):
        await self.node_a.send_to("veh-B", {"type": "route_update", "payload": {"route": [1, 2, 3]}})
        await asyncio.sleep(0.5)
        self.assertTrue(any(m.get('type') == 'route_update' for m in self.messages_b))


if __name__ == '__main__':
    unittest.main()

