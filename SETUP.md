# One-Time Setup — Federal Marketplace Index
About one hour, once. Steps 1–2 must be done by the organization; the rest can
be done by any team member.

1. DOMAIN. Register federalmarketplaceindex.org (and the .com, redirected).
2. GITHUB ORGANIZATION. Create a free GitHub organization (e.g.,
   "federal-marketplace-index") at github.com. Create a new PUBLIC repository
   in it named `federal-marketplace-index`.
3. GITHUB DESKTOP. Install GitHub Desktop (desktop.github.com) on the team
   machine and sign in. File > Clone repository > select the new repo.
4. LOAD THE FILES. Copy the contents of this starter package into the cloned
   folder. In GitHub Desktop: Commit to main ("initial site"), Push origin.
5. TURN ON PAGES. On github.com, in the repository: Settings > Pages >
   Source: "Deploy from a branch" > Branch: main, Folder: /docs > Save.
6. CONNECT THE DOMAIN. Still in Settings > Pages: enter
   federalmarketplaceindex.org as the custom domain and Save. At your domain
   registrar, create these DNS records:
     A     @    185.199.108.153
     A     @    185.199.109.153
     A     @    185.199.110.153
     A     @    185.199.111.153
     CNAME www  <organization>.github.io
   Back in Settings > Pages, once the DNS check passes, check
   "Enforce HTTPS". (DNS can take up to a day; usually under an hour.)
7. VERIFY. Visit https://federalmarketplaceindex.org — the Index is live.
   From now on, updates follow RUNBOOK.md.
