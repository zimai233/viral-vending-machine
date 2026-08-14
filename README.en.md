# Viral Vending Machine · Social Media Copywriting Skill

> Drop in a topic, get a viral-ready post. Generates original copy in your **persona's voice** using a **benchmark case library** — with auto-scraping of benchmark creators, voice-to-text transcription, topic analysis, and anti-plagiarism checks. All via conversation, no CLI needed.

## What It Does

| You Say | Result |
|---|---|
| "Write copy about XX" | 3-5 original drafts (title / key point / script / hashtags) from your persona + case library |
| "Benchmark @creator (or paste link)" | Auto-crawl that creator's top videos of recent N months → transcribe speech → update case library |
| "Scrape the 'XX' niche" | Crawl trending content by keyword |
| "Update case library" | Re-crawl all benchmark accounts' latest top posts (idempotent) |

## Core Features

- **Persona-driven**: `assets/persona.md` defines who you are and how you talk; generation strictly follows it
- **Case library**: `assets/cases/` — one file per benchmark creator with full transcripts + framework tags; new creators auto-appended
- **Style guide**: `references/style-guide.md` — distilled 6 content forms (reveal / avoid / list / quote / contrast / opinion) + opening hooks + body structure + voice patterns + CTA
- **Anti-plagiarism**: `scripts/similarity.py` n-gram similarity check, flags drafts needing rewrite
- **Pipeline**: Douyin direct API (bypasses MediaCrawler signing bug) + Whisper speech transcription

## Installation (New Machine)

**Prereqs**: Python 3.11+, uv, ffmpeg, Node 16+, Git Bash (Windows) or bash (macOS/Linux), Chrome

```bash
# 1. Place the skill into opencode's skills directory
#    Windows:  %USERPROFILE%\.config\opencode\skills\viral-vending-machine\   or project-level .opencode\skills\
#    macOS/Linux: ~/.config/opencode/skills/viral-vending-machine/

# 2. One-shot bootstrap (deps + clone MediaCrawler + Chrome login guide)
bash scripts/setup.sh

# 3. Fill in your personal data (persona + case library)
#    assets/persona.md           ← your writing persona
#    assets/cases/               ← your benchmark case library

# 4. Configure Chrome debugging (one-time, for Douyin crawling)
#    chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<fixed-dir>
#    Log into Douyin; cookies persist, subsequent crawls reuse the session
```

## Structure

```
viral-vending-machine/
├── SKILL.md              # 3-scenario orchestration (write / benchmark / update)
├── assets/
│   ├── persona.md        # Writing persona (user data)
│   └── cases/            # Case library (user data, per-creator + index.md)
├── references/
│   ├── style-guide.md    # Expression style guide (required reading)
│   ├── frameworks.md     # Topic directions / writing frameworks (user data)
│   ├── platform-rules.md # Per-platform copy rules
│   └── originality.md    # Anti-plagiarism checklist
├── scripts/
│   ├── douyin_api.py     # Douyin crawler (API + cookies, bypasses signing bug)
│   ├── transcribe.py     # Speech-to-text (Whisper + URL refresh)
│   ├── update_library.py # Crawl JSON → case library (idempotent)
│   ├── similarity.py     # Anti-plagiarism similarity check
│   ├── collect.py        # Xiaohongshu crawler (MediaCrawler wrapper)
│   ├── setup.sh          # One-shot bootstrap
│   └── run_tests.py      # Offline tests
└── tools/MediaCrawler    # Crawler engine (auto-cloned by setup.sh)
```

## Tests

```bash
python scripts/run_tests.py
```

## Compliance Notes

- For learning/research and personal content reference only; control crawl frequency and respect platform ToS.
- Use creator content for direction/structure reference only — never copy text or repost videos.
- The crawler is for learning/research only (per MediaCrawler's license).
- Generated content must comply with each platform's community guidelines and advertising laws.

## License

MIT (except `tools/MediaCrawler`, which retains its original license)
