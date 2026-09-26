# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-09-26

### Added

- A print dialog with copies, color mode and page range (`1-3,5`).
- Markdown (`.md`) files are accepted and sent to the CUPS text filter.

## [1.0.0] - 2026-09-26

### Added

- `cups_print` Nextcloud app: a **Print** action in the Files app for PDF, PNG,
  JPEG and text files, with an admin settings panel for the relay URL and token.
- CUPS print relay (`server/`): standard-library Python service, Dockerfile and
  `compose.yaml`, bearer-token authentication, client allowlist, size limit.
- Japanese translations (`l10n/ja.json`).
- CI (bundle build, PHP lint, relay tests, container build) and a signed
  release workflow for the Nextcloud App Store.
