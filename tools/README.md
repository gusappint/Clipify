# Bundled runtime tools

`deno` is optional during development and recommended for release builds. Run:

```bash
python scripts/fetch_deno.py
```

The build script embeds the downloaded executable into the portable app. FFmpeg
is supplied by the platform-specific `imageio-ffmpeg` wheel.
