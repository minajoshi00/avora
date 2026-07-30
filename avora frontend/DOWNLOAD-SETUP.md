# AVORA Download System Setup

## Overview
- DownloadCenter.tsx: Main download UI with progress tracking
- versions.ts: Version configuration (URLs, metadata, checksums)
- platform-detection.ts: OS/architecture detection

## Configuring Download URLs
Edit src/lib/versions.ts and update the url fields for each platform.

## Hosting Options
- GitHub Releases (recommended for open source)
- Cloudflare R2 (best performance, no egress fees)
- AWS S3 + CloudFront (enterprise)
- Vercel Blob Storage

## Release Process
To release a new version:
1. Edit ONLY src/lib/versions.ts
2. Add new version entry with isLatest: true
3. Update download URLs
4. Upload installer to hosting provider
5. Deploy to Vercel