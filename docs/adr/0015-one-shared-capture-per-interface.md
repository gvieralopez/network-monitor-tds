# One shared capture per interface

Listener plugins ask `capture()` for packets with a `PacketFilter`: a BPF expression for the kernel and a predicate that picks the plugin's packets in Python. All listeners on an interface share one raw socket, whose BPF filter is the union of the subscribers' expressions. The socket is reopened whenever that union changes, so turning a listener off also stops capturing its traffic.

The hubs live in a module-level registry rather than being injected through `PluginContext`. Plugins are loaded from entry points and the SDK is public, so a shared capture service in the context would be an SDK change for something only the built-in listeners need.

## Consequences

- The new socket opens before the old one closes. If it cannot open, the old capture keeps running: a new subscriber gets the error, and a leaving one leaves the wider filter in place.
- During a switch both sockets can deliver the same packet once. That is harmless: the ARP listener throttles per device, and a repeated sighting of a known device only refreshes its last-seen time.
- A predicate must match no more than its BPF expression: the socket also carries the other listeners' traffic, and a wider predicate would receive it.
