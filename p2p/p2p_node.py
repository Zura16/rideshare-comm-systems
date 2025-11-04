"""
Asyncio-based peer-to-peer node for decentralized discovery and messaging.
"""
from __future__ import annotations

import asyncio
import json
import socket
import struct
import time
import contextlib
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple, Any, List


@dataclass
class PeerInfo:
    node_id: str
    host: str
    port: int
    last_seen: float = field(default_factory=lambda: time.time())
    failures: int = 0

    def endpoint(self) -> Tuple[str, int]:
        return self.host, self.port


class P2PNode:
    """
    P2PNode coordinates UDP multicast discovery and a TCP server for application messages.

    Messages are JSON lines. Minimal schema:
      {"type": "location_update", "from": <node_id>, "payload": {...}}

    Callbacks: set on_message callback to receive decoded message dicts.
    """

    def __init__(
        self,
        node_id: str,
        listen_host: str = "0.0.0.0",
        listen_port: int = 0,
        mcast_group: str = "224.0.0.250",
        mcast_port: int = 50000,
        announce_interval: float = 1.0,
        peer_timeout: float = 5.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.node_id = node_id
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.mcast_group = mcast_group
        self.mcast_port = mcast_port
        self.announce_interval = announce_interval
        self.peer_timeout = peer_timeout
        self.loop = loop or asyncio.get_event_loop()

        self._server: Optional[asyncio.AbstractServer] = None
        self._announce_task: Optional[asyncio.Task] = None
        self._prune_task: Optional[asyncio.Task] = None
        self._discovery_transport: Optional[asyncio.transports.DatagramTransport] = None
        self._discovery_protocol: Optional[asyncio.DatagramProtocol] = None
        self._send_sock: Optional[socket.socket] = None

        self._peers: Dict[str, PeerInfo] = {}
        self._peers_lock = asyncio.Lock()
        self._on_message: Optional[Callable[[Dict[str, Any]], None]] = None

        # Resolved public address for announcements (best-effort)
        detected = self._detect_bind_ip()
        self._announce_host = listen_host if listen_host not in ("0.0.0.0", "") else detected
        self._mcast_if = self._announce_host

    def _detect_bind_ip(self) -> str:
        # Try to detect a reasonable outbound IP for announcements
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # Public API
    @property
    def peers(self) -> Dict[str, PeerInfo]:
        return dict(self._peers)

    def on_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._on_message = callback

    async def start(self) -> None:
        # Start TCP server
        self._server = await asyncio.start_server(self._handle_client, self.listen_host, self.listen_port)
        sockets = self._server.sockets
        assert sockets and sockets[0].getsockname()
        self.listen_port = sockets[0].getsockname()[1]

        # Start UDP multicast discovery listener and sender
        await self._start_discovery()

        # Background tasks
        self._announce_task = self.loop.create_task(self._announce_loop())
        self._prune_task = self.loop.create_task(self._prune_loop())

    async def stop(self) -> None:
        if self._announce_task:
            self._announce_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._announce_task
        if self._prune_task:
            self._prune_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._prune_task
        if self._discovery_transport:
            self._discovery_transport.close()
            self._discovery_transport = None
        if self._send_sock:
            try:
                self._send_sock.close()
            except Exception:
                pass
            self._send_sock = None
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def broadcast(self, message: Dict[str, Any]) -> None:
        # Send to all known peers concurrently
        await asyncio.gather(*(self._send_message(peer, message) for peer in list(self._peers.values())), return_exceptions=True)

    async def send_to(self, node_id: str, message: Dict[str, Any]) -> None:
        peer = self._peers.get(node_id)
        if not peer:
            raise KeyError(f"Unknown peer {node_id}")
        await self._send_message(peer, message)

    # Internals
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peername = writer.get_extra_info('peername')
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not line:
                return
            data = json.loads(line.decode('utf-8').strip())
            if isinstance(data, dict) and data.get("type") == "ping":
                # Simple liveness check
                writer.write((json.dumps({"type": "pong"}) + "\n").encode('utf-8'))
                await writer.drain()
            else:
                if self._on_message:
                    self._on_message(data)
        except (asyncio.TimeoutError, json.JSONDecodeError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _send_message(self, peer: PeerInfo, message: Dict[str, Any]) -> None:
        payload = dict(message)
        payload.setdefault("from", self.node_id)
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(peer.host, peer.port), timeout=2.0)
            writer.write((json.dumps(payload) + "\n").encode('utf-8'))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            peer.failures = 0
        except Exception:
            peer.failures += 1

    async def _start_discovery(self) -> None:
        # Receiver socket with multicast membership
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:
            pass
        recv_sock.bind(("", self.mcast_port))
        group = socket.inet_aton(self.mcast_group)
        # Join group on all interfaces (default)
        try:
            mreq_any = struct.pack('4s4s', group, socket.inet_aton('0.0.0.0'))
            recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq_any)
        except Exception:
            pass
        # Also join on the specific local interface to support Windows loopback
        try:
            mreq_local = struct.pack('4s4s', group, socket.inet_aton(self._mcast_if))
            recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq_local)
        except Exception:
            pass
        # Enable loopback so local testing discovers itself and other local peers
        recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        recv_sock.setblocking(False)

        class DiscoveryProtocol(asyncio.DatagramProtocol):
            def __init__(self, outer: 'P2PNode') -> None:
                self.outer = outer

            def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
                try:
                    msg = json.loads(data.decode('utf-8'))
                    if not isinstance(msg, dict) or msg.get('type') != 'hello':
                        return
                    node_id = msg.get('node_id')
                    if node_id == self.outer.node_id:
                        return
                    host = msg.get('host') or addr[0]
                    port = int(msg.get('port'))
                    asyncio.create_task(self.outer._register_peer(node_id, host, port))
                except Exception:
                    pass

        self._discovery_transport, self._discovery_protocol = await self.loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self), sock=recv_sock
        )

        # Sender socket
        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # TTL 1 keeps traffic on local network
        self._send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        self._send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        # Choose outgoing interface for multicast (important on Windows / loopback)
        try:
            self._send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self._mcast_if))
        except Exception:
            pass
        # Bind sender to a local address (optional but helps Windows)
        try:
            self._send_sock.bind((self._announce_host, 0))
        except Exception:
            pass
        self._send_sock.setblocking(False)

    async def _register_peer(self, node_id: str, host: str, port: int) -> None:
        async with self._peers_lock:
            info = self._peers.get(node_id)
            if info is None or (info.host, info.port) != (host, port):
                self._peers[node_id] = PeerInfo(node_id=node_id, host=host, port=port, last_seen=time.time())
            else:
                info.last_seen = time.time()

    async def _announce_loop(self) -> None:
        while True:
            try:
                hello_obj = {
                    'type': 'hello',
                    'node_id': self.node_id,
                    # If listening on all interfaces, prefer receiver's source address; else, send explicit host
                    'host': None if self.listen_host in ("0.0.0.0", "") else self._announce_host,
                    'port': self.listen_port,
                }
                hello = json.dumps(hello_obj).encode('utf-8')
                if self._send_sock is not None:
                    self._send_sock.sendto(hello, (self.mcast_group, self.mcast_port))
            except Exception:
                pass
            await asyncio.sleep(self.announce_interval)

    async def _prune_loop(self) -> None:
        while True:
            await asyncio.sleep(self.announce_interval)
            now = time.time()
            to_remove: List[str] = []
            async with self._peers_lock:
                for pid, p in self._peers.items():
                    if now - p.last_seen > self.peer_timeout:
                        to_remove.append(pid)
                for pid in to_remove:
                    self._peers.pop(pid, None)


# Convenience runner for manual testing
async def _demo() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Run a P2P node")
    parser.add_argument('--id', required=True, help='Node ID, e.g., vehicle-1')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--mgroup', default='224.0.0.250')
    parser.add_argument('--mport', type=int, default=50000)
    args = parser.parse_args()

    node = P2PNode(node_id=args.id, listen_host=args.host, listen_port=args.port, mcast_group=args.mgroup, mcast_port=args.mport)

    def on_msg(msg: Dict[str, Any]) -> None:
        print(f"[{args.id}] received: {msg}")

    node.on_message(on_msg)
    await node.start()
    print(f"Node {args.id} listening on TCP {node.listen_port}, announcing on {args.mgroup}:{args.mport}")

    # Periodically broadcast a sample message
    i = 0
    try:
        while True:
            await asyncio.sleep(2)
            i += 1
            await node.broadcast({"type": "location_update", "seq": i, "payload": {"lat": 33.7838, "lon": -118.1141}})
    except KeyboardInterrupt:
        pass
    finally:
        await node.stop()


if __name__ == '__main__':
    asyncio.run(_demo())
