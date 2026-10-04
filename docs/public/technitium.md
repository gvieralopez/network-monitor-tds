# Technitium DHCP integration

If [Technitium DNS Server](https://technitium.com/dns/) is your DHCP server, Network Monitor TDS can import the hostnames from its leases. Lease hostnames are the best names available: they come straight from the devices and from your reservations.

The integration only reads. It never changes anything in Technitium, and it never marks a device online by itself; a lease only adds a name to a device the monitor has already seen on the network.

## Set it up

1. In Technitium, open **Administration → Sessions** and create an API token.
2. In Network Monitor TDS, open **Settings → Sources → Technitium DHCP leases → Settings** and fill in:
   - **Server address**: the Technitium web console, for example `http://192.168.1.10:5380`.
   - **API token**: the token from step 1.
   - **Verify TLS certificate**: turn it off only if you use HTTPS with a self-signed certificate.
3. Save, then turn the plugin on.

The status line under the plugin shows "Working · last success …" once a poll succeeds, or the error from Technitium (for example an invalid token).

From the command line instead:

```bash
nmtds plugins set technitium url=http://192.168.1.10:5380 token=<your token>
nmtds plugins enable technitium
```

The token is stored in the monitor's database, so keep the data folder and its backups private.
