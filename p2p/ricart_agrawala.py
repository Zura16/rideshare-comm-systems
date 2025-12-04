# p2p/ricart_agrawala.py

import asyncio
from typing import Dict, Any, Optional, Set

from p2p.p2p_node import P2PNode


class RicartAgrawalaMutex:
    def __init__(self, node: P2PNode):
        self.node = node
        self.node.ricart = self   # Register with P2PNode

        self.clock = 0
        self.state = "RELEASED"        # RELEASED, WANTED, HELD
        self.request_ts: Optional[int] = None

        self.pending: Set[str] = set()
        self.deferred: Set[str] = set()

        self._lock = asyncio.Lock()
        self._cs_event = asyncio.Event()
        self._cs_event.set()

    async def request_cs(self, resource="default"):
        async with self._lock:
            self.clock += 1
            self.state = "WANTED"
            self.request_ts = self.clock

            # snapshot of peers at request time
            self.pending = set(self.node.peers.keys())

            # send request message
            req = {
                "type": "ra_request",
                "from": self.node.node_id,
                "ts": self.request_ts,
                "resource": resource,
            }
            await self.node.broadcast(req)

            if not self.pending:
                self.state = "HELD"
                return

            self._cs_event.clear()

        await self._cs_event.wait()

    async def release_cs(self, resource="default"):
        async with self._lock:
            self.state = "RELEASED"
            to_reply = list(self.deferred)
            self.deferred.clear()

        for pid in to_reply:
            await self.node.send_to(pid, {
                "type": "ra_reply",
                "from": self.node.node_id,
                "resource": resource
            })

    async def handle_message(self, msg: Dict[str, Any]):
        mtype = msg["type"]
        sender = msg["from"]

        if mtype == "ra_request":
            await self._handle_request(sender, msg)

        elif mtype == "ra_reply":
            await self._handle_reply(sender)

    async def _handle_request(self, sender: str, msg: Dict[str, Any]):
        ts = msg["ts"]
        #debug logging
        print(f"[{self.node.node_id}] <- RA REQUEST from {sender} (ts={ts})")


        async with self._lock:
            self.clock = max(self.clock, ts) + 1

            defer = False
            if self.state == "HELD":
                defer = True
            elif self.state == "WANTED":
                my_key = (self.request_ts, self.node.node_id)
                other_key = (ts, sender)
                if my_key < other_key:
                    defer = True

            if defer:
                self.deferred.add(sender)
                return

        # Only reply if peer is known; if not, defer the reply
        if sender in self.node.peers:
            await self.node.send_to(sender, {
                "type": "ra_reply",
                "from": self.node.node_id
            })
        else:
            print(f"[{self.node.node_id}] deferring reply because {sender} not in peers yet")
            self.deferred.add(sender)
            return

    async def _handle_reply(self, sender: str):
        print(f"[{self.node.node_id}] <- RA REPLY from {sender}")

        # Ignore replies from peers not fully discovered yet
        if sender not in self.node.peers:
            print(f"[{self.node.node_id}] ignoring reply from unknown peer {sender}")
            return

        # Normal logic
        if sender in self.pending:
            self.pending.remove(sender)

        if not self.pending and self.state == "WANTED":
            self.state = "HELD"
            self._cs_event.set()