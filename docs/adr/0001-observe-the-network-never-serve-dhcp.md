# Observe the network, never serve DHCP or DNS

The router stays a plain gateway and Technitium keeps serving DHCP and DNS. Network Monitor TDS only watches: it can read Technitium's leases through an integration plugin, but it never answers DHCP or DNS itself. Bundling a DHCP server was considered, because it would make discovery trivial, but passive DHCP sniffing already gives the hostnames and fingerprints, and keeping the monitor out of the critical path means it can crash, restart or be upgraded without anyone on the network noticing.
