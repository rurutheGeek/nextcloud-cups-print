# CUPS Print for Nextcloud

Print files from the Nextcloud Files app through a small CUPS relay.

This repository contains two parts that belong together:

| Directory | Part |
| --- | --- |
| repository root | the **cups_print** Nextcloud app (PHP + a bundled file action) |
| [`server/`](server/) | the **CUPS print relay** (Python standard library, Docker image) |

A short Japanese summary is at the end of this file.

## How it works

```
Files app ──"Print"──▶ cups_print (Nextcloud app)
                          │  POST /print  (bearer token, file bytes)
                          ▼
                    print relay ──▶ `lp -d <queue>` ──▶ CUPS ──▶ printer
```

The relay is a single Python file with no dependencies outside the standard
library. It reduces the client-supplied filename to a safe title, accepts PDF,
PNG, JPEG, plain text and Markdown files (Markdown goes through the CUPS text
filter), enforces a size limit and runs `lp` against the configured queue.
Only the selected file leaves Nextcloud, and only to the relay URL that your
administrator configured.

## Quick start

### 1. Start the relay

```bash
cd server
cp .env.example .env
# edit .env: PRINT_API_TOKEN, PRINT_QUEUE, optional PRINT_API_ALLOWED, CUPS_SERVER
docker compose up -d --build
curl http://localhost:6320/healthz
```

Or build the image yourself:

```bash
docker build -t cups-print-relay server/
```

Anything that can send an HTTP POST can use the relay, not just Nextcloud:

```bash
curl -H "Authorization: Bearer $PRINT_API_TOKEN" \
     -H 'X-Print-Filename: report.pdf' \
     --data-binary @report.pdf \
     http://relay.example.net:6320/print
```

### 2. Install the app

From the [Nextcloud App Store](https://apps.nextcloud.com/apps/cups_print)
(search for *CUPS Print*), or manually:

```bash
tar -xzf cups_print.tar.gz -C /var/www/html/custom_apps/
occ app:enable cups_print
```

The archive is published on the [releases page](../../releases) of this
repository for every version.

### 3. Configure

As an administrator open *Administration settings → CUPS Print* and set:

- **Relay URL** — e.g. `http://192.168.1.10:6320`
- **Relay token** — the same value as `PRINT_API_TOKEN` in the relay's `.env`

Saving runs a health check against the relay and reports the result on the
same page. No `occ config:app:set` needed.

## Relay configuration

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `PRINT_API_TOKEN` | yes | – | shared secret (`Authorization: Bearer …`) |
| `PRINT_QUEUE` | yes | – | CUPS queue name, as shown by `lpstat -p` |
| `PRINT_API_ALLOWED` | no | empty | comma-separated client addresses; empty accepts any client with the token |
| `PRINT_API_BIND` | no | `0.0.0.0` | listen address |
| `PRINT_API_PORT` | no | `6320` | listen port |
| `PRINT_API_MAX_BYTES` | no | `52428800` | maximum document size (50 MiB) |
| `CUPS_SERVER` | no | local CUPS | passed to `lp`, e.g. `cups.example.net:631` |

### API

- `GET /healthz` — `200 {"status": "ok"}`
- `POST /print` — body is the document
  - `Authorization: Bearer <token>` (required)
  - `X-Print-Filename`: URL-encoded filename; the extension decides the format
  - `X-Print-Copies`: 1–99 (default 1)
  - `X-Print-Color`: `color` or `monochrome` (default `color`)
  - `X-Print-Ranges`: optional CUPS page range, e.g. `1-3,5` (PDF/text)
  - answers `{"job": "<lp job id>"}`

## Security notes

- Run the relay inside your own network and put a TLS terminator in front of it
  if it must cross a network boundary; `lp` itself does not encrypt anything.
- Keep `PRINT_API_ALLOWED` set to your Nextcloud server's address when both are
  on a trusted LAN.
- The app refuses files the user may not read, and only forwards files whose
  extension is printable.

## Development

```bash
npm ci && npm run build        # rebuild js/cups_print.js with esbuild
python3 -m unittest discover -s server/tests -v
docker build -t cups-print-relay:dev server/
```

The bundle in `js/` is committed because Nextcloud does not build apps on
install. CI rebuilds it and fails when the committed file is stale.

For a real-instance check, copy the repository into
`custom_apps/cups_print/` of a Nextcloud 33+ installation, run
`occ app:enable cups_print` and use *Administration settings → CUPS Print*.

## Releasing to the Nextcloud App Store

The store requires an app-specific certificate and a signed archive.

1. Generate a key and CSR (once):

   ```bash
   mkdir -p ~/.nextcloud/certificates
   openssl req -nodes -newkey rsa:4096 \
     -keyout ~/.nextcloud/certificates/cups_print.key \
     -out ~/.nextcloud/certificates/cups_print.csr \
     -subj "/CN=cups_print"
   ```

2. Open a pull request with the `.csr` at
   [nextcloud/app-certificate-requests](https://github.com/nextcloud/app-certificate-requests)
   and put the signed `cups_print.crt` next to the key.

3. Add the repository secrets `APP_PRIVATE_KEY`, `APP_PUBLIC_CRT` and
   `APPSTORE_TOKEN` (from <https://apps.nextcloud.com/account/token>), and set
   the repository variable `APPSTORE_ENABLED=true`.

4. Bump the version in `appinfo/info.xml` (and `CHANGELOG.md`), create a GitHub
   release tagged `v<version>` and publish it. The
   [release workflow](.github/workflows/release.yml) builds, signs and attaches
   `cups_print.tar.gz`, then pushes it to the store.

Until `APPSTORE_ENABLED` is set, the workflow only attaches the archive to the
GitHub release.

## License

[AGPL-3.0-or-later](LICENSE).

---

## 日本語の概要

Nextcloud の Files アプリに「印刷」アクションを追加する `cups_print` アプリと、
その受け先となる小さな CUPS 中継API（`server/`、Python 標準ライブラリのみ）の
リポジトリです。

- 中継APIは `docker compose up -d` で起動し、`PRINT_API_TOKEN`・`PRINT_QUEUE`・
  `CUPS_SERVER` を `.env` で設定します
- アプリは管理画面（*管理設定 → CUPS印刷*）で中継APIのURLとトークンを設定します。
  保存時にヘルスチェックして結果を表示します
- PDF・PNG・JPEG・テキストのみ、50MiBまで、トークン認証つき。ファイルは
  自分のネットワークの外へ出ません
- App Store 公開にはアプリ専用の証明書（CSRを
  [app-certificate-requests](https://github.com/nextcloud/app-certificate-requests)
  へPR）と、GitHub Release からの署名・アップロードが必要です
