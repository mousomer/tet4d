# The website (Cloudflare Pages)

When a game is ready for a public home: a site with a front page at `/` and the installable game at `/play/`,
deployed by Cloudflare Pages straight from the repository. Dungeon Raid's and Crawl's `tools/site/` are the models
(Crawl's is the plainer one to copy; Dungeon Raid's adds a tribute page and a play counter).

## The build

`tools/site/build.py`, plain Python 3 with no packages, so Cloudflare can run it as the build command. It builds
`site/` (git-ignored):

- `/`: the front page (a stand-in until its design is decided with the owner; at launch, the game page with the dev
  blog and the post mortem's conclusions).
- `/play/`: the game, installable. Its files at their repo paths (the artifact build's list), the page with the app's
  head tags, a web app manifest (full screen, portrait), the icons, a service worker that caches the game on the first
  visit so it opens offline (a cache named by the build's content hash: a new build installs beside the old one and
  takes over at the next launch, so a game in progress never mixes two versions).
- `_headers`: Cloudflare's cache rules.
- `--url https://<project>.pages.dev/` adds the share tags (og:url, og:image at its absolute address).

`node tools/site/check.mjs site` checks it headless: the front page, the boot, the service worker in control, the
install criteria, an offline boot.

**The coming-soon gate** (Dungeon Raid, 2026-10-12): connecting a repository deploys at once, so a Pages build
(`CF_PAGES=1`, set by Cloudflare) without the project variable `SITE_LIVE=1` publishes only a coming-soon page (the
logo, COMING SOON, `noindex`). The owner can connect whenever it suits them; nothing else goes public before launch.
Put the gate in before the owner connects, on the branch the site builds from.

## Who does what

- **Claude never handles a Cloudflare API token.** The sessions' Cloudflare connector reaches Workers, KV, R2, D1 and
  the docs, but has no Pages tools, so it cannot deploy. The owner connects the project in the dashboard, once.
- **The production branch is `release`.** It is what the site serves: Claude pushes it only on the owner's go-ahead
  (a fast-forward to the version being released). Preview deployments stay off until launch.
- **The name** is the owner's pick: `<name>.pages.dev` has to be free, and the plain names were taken for both games
  (dungeon-raid, crawl). Check a few before writing the ticket: `curl -s -o /dev/null -m 15 -w "%{http_code}"
  https://<name>.pages.dev/` answers `000` for a free name; a taken one serves someone's page. List the free ones.
- **The steps are the owner's ticket**: a card of the type `task` on the board (`board/`), in To review, linking
  https://dash.cloudflare.com.

## The ticket's text (fill in the repository and the free names)

> Until launch the site shows only the logo and COMING SOON, so connecting it now puts nothing else in public.
> 1. In the Cloudflare dashboard: Workers & Pages, Create application, the Pages tab, Import an existing Git repository.
> 2. Pick the GitHub account, then the repository `<repo>`, then Begin setup. (If it isn't in the list: Configure the
>    GitHub account there and give Cloudflare's app access to it too.)
> 3. Project name: your pick; it becomes `<name>.pages.dev`. Free today: `<names>`.
> 4. Production branch: release.
> 5. Framework preset: None. Build command: `python3 tools/site/build.py --url https://<name>.pages.dev/` (with your
>    project name in the address). Build output directory: `site`
> 6. Save and Deploy. In about a minute the address shows the logo and COMING SOON.
> 7. Then, in the project's Settings under Build (Branch control), set preview deployments to None.
>
> When it's done, put the address in your note and move this card to Ready for Claude. At launch you add one
> variable, SITE_LIVE = 1 (Settings, Variables and Secrets, Production), and I push the release on your go-ahead.

A game with a play counter adds a step (Dungeon Raid's 8): Settings, Bindings, Add, KV namespace, variable name
`PLAYS`, a new namespace; until then the page hides the count.

When the owner moves the card to Ready for Claude: open the address and check the coming-soon page, record the
address in the project's CLAUDE.md (Run) and the build command with it, and move the card to Done.

## At launch

1. The post mortem first (`post-mortem/`), so its conclusions go into the front page.
2. The owner adds `SITE_LIVE = 1` (Settings, Variables and Secrets, Production).
3. On the owner's go-ahead, Claude fast-forwards `release` and pushes it; Cloudflare builds it in about a minute.
4. Check the live site: `node tools/site/check.mjs` against a fresh build, then the address itself on a phone
   (install it, open it offline).
5. After launch, each update is the same push of `release`, on the go-ahead.
