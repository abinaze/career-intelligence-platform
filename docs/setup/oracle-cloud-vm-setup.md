# Oracle Cloud Always Free VM setup (backend hosting)

Chosen over Hugging Face Spaces, Google Cloud Run, Render, Koyeb, and
Fly.io after actually researching current (2026) pricing and behavior
rather than assuming: it's the only option that doesn't scale to zero or
sleep at all, because it's a real always-on VM, not serverless compute —
see the comparison in `docs/deployment/guide.md`. The trade-off, stated
plainly: you're managing a real server (OS updates, Docker, security)
yourself, not a managed platform.

**This guide describes a real, multi-step cloud console workflow that
wasn't tested end-to-end against a live Oracle account while writing
it** (no Oracle Cloud credentials were available in the environment this
was built in) — it's based on Oracle's own current documentation and
widely-corroborated, recent (2026) reports of exactly where people get
stuck. Treat the first real walkthrough as the actual test, and if a step
doesn't match what you see, that's more likely Oracle's console having
changed than this guide being wrong on purpose.

## 1. Create an Oracle Cloud account

[cloud.oracle.com/free](https://www.oracle.com/cloud/free/) — requires a
credit card for identity verification, same as Google Cloud Run would.
You will not be charged as long as you stay within the Always Free
limits described below.

## 2. Create the compute instance

**Compute → Instances → Create instance.**

- **Image**: Ubuntu (22.04 or 24.04 LTS) — simpler than Oracle Linux for
  this guide's Docker-based steps, and what the commands below assume.
- **Shape**: click **Change shape** → **Ampere** → **VM.Standard.A1.Flex**.
  As of this writing, the Always Free allocation for this shape is 2
  OCPUs / 12 GB RAM total (recently reduced from 4 OCPU/24GB — check
  the console's own free-eligible indicator, since Oracle can adjust
  this without much notice). Set the instance to use the full free
  allocation.
- **Networking**: use the default VCN, and check **Assign a public
  IPv4 address**.
- **SSH keys**: either let Oracle generate a key pair for you (download
  both immediately — the private key is only shown once) or paste your
  own public key. You'll need a private key either way to SSH in.

Click **Create**.

### If you get an "Out of capacity" error

This is a very common, well-documented issue specifically with the
Ampere A1 free shape — Oracle doesn't guarantee capacity for free-tier
ARM instances in every region/availability domain. If it happens:

- Try a different **Availability Domain** in the same region (the
  instance creation form lets you pick).
- Try a different region entirely (you can change your tenancy's home
  region only once, but you can still have resources in other
  subscribed regions).
- As a fallback with no capacity issues but far less headroom: the
  **VM.Standard.E2.1.Micro** (AMD) shape is also Always Free (1/8 OCPU,
  1 GB RAM) and essentially always available — workable for this app at
  rest (most of the ML dependencies are lazy-loaded, see
  `docs/architecture/byos.md`'s embeddings note) but with much less
  headroom under any real load. Prefer the Ampere shape if you can get it.

## 3. Open the required ports — twice

Oracle Cloud has **two** separate firewalls, and both have to allow
traffic, or requests silently drop with no error indicating which one
blocked it. This trips up a lot of people new to Oracle Cloud
specifically (it's not how AWS/GCP/Azure's default images behave) and is
the single most common reason "everything looks right but I can't reach
my server."

**a) The VCN Security List** (cloud firewall): **Networking → Virtual
Cloud Networks → (your VCN) → Security Lists → Default Security List →
Add Ingress Rules**. Add rules allowing TCP on ports `22` (SSH — likely
already open), `80`, and `443` from source `0.0.0.0/0`.

**b) The instance's own OS-level firewall**: Ubuntu images on Oracle
Cloud ship with `iptables` rules that block inbound traffic by default,
independent of the security list above. SSH in and run:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # persist across reboots, if installed
```

If `netfilter-persistent` isn't installed (`sudo apt install
iptables-persistent` will prompt to save current rules), the rules above
won't survive a reboot — worth installing it rather than re-running the
`iptables -I` commands by hand after every restart.

## 4. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# log out and back in (or `newgrp docker`) for the group change to apply
docker compose version   # confirm the Compose plugin is present
```

## 5. Clone the repo and configure

```bash
git clone https://github.com/abinaze/career-intelligence-platform.git
cd career-intelligence-platform
cp infrastructure/docker/.env.production.example infrastructure/docker/.env.production
nano infrastructure/docker/.env.production   # fill in real values
```

Same variables as the fully-self-hosted `docker-compose.prod.yml` path
(`docs/deployment/guide.md`'s Self-Hosted section) — `SECRET_KEY`,
`POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and the OAuth broker credentials
if you want BYOS working. `FRONTEND_URL` should point at wherever the
frontend actually ends up (Vercel, per the main guide) — this VM only
hosts the backend.

## 6. Point a domain at this VM

Caddy (used here instead of nginx specifically for this path — see
`infrastructure/docker/Caddyfile`'s header comment) needs a real DNS
record to automatically obtain a Let's Encrypt certificate. Create an A
record (and AAAA if the instance has an IPv6 address) pointing your
chosen subdomain — e.g. `api.your-domain.example.com` — at this VM's
public IP. Then edit `infrastructure/docker/Caddyfile` and replace the
placeholder domain with your real one.

## 7. Bring up the stack

```bash
docker compose -f infrastructure/docker/docker-compose.oracle-vm.yml \
  --env-file infrastructure/docker/.env.production up -d
```

This starts Postgres, Redis, the backend (which runs pending Alembic
migrations automatically on start — see
`apps/backend/docker-entrypoint.sh`), and Caddy. First start will take a
minute or two while Caddy requests its certificate — watch it with:

```bash
docker compose -f infrastructure/docker/docker-compose.oracle-vm.yml logs -f caddy
```

Once it's up: `https://api.your-domain.example.com/health` should
respond.

## 8. Set up push-to-deploy from GitHub Actions

See `.github/workflows/deploy-oracle-vm.yml`'s header comment for the
exact steps (generating a dedicated deploy key, adding it to this VM's
`~/.ssh/authorized_keys`, and adding three GitHub repo secrets). Once
that's done, pushes to `main` touching `apps/backend/**` rebuild and
restart just the backend container over SSH — Postgres, Redis, and
Caddy keep running untouched.

## Ongoing maintenance (this is the actual cost of "zero sleep")

Nothing here auto-updates. Worth doing periodically, since this is a
real server now, not a managed platform:

- `sudo apt update && sudo apt upgrade` for OS security patches.
- `docker system prune` occasionally — the free tier's boot volume is
  limited (check your instance's allotted storage in the console), and
  old, unused Docker images/build cache can fill it faster than expected.
- Keep an eye on actual resource usage if you're near the Always Free
  compute ceiling — Oracle's free tier is generous but not unlimited,
  and unlike Cloud Run/Koyeb there's no automatic scaling to fall back
  on if this one VM gets overwhelmed.
