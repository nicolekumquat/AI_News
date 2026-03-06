# AI Daily Digest

A command-line tool for aggregating daily AI news from multiple sources into a formatted, readable digest.

## Features

- **Automatic News Fetching**: Retrieves AI news from 10+ sources including HackerNews, Reddit, ArXiv, and AI company blogs
- **48-Hour Freshness**: Only includes articles published within the last 48 hours
- **Source Attribution**: Every article includes source name, URL, and publication date
- **Smart Caching**: Caches processed digests locally for fast retrieval
- **Retry Logic**: 3 retries with exponential backoff for failed source fetches
- **Human-Readable Output**: Clean, formatted CLI output optimized for reading
- **Source Management**: Add, remove, enable, and disable news sources via CLI
- **Podcast Summarization**: Download, transcribe, and summarize podcast episodes locally

## Installation

### Requirements

- Python 3.11 or higher
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Package

```bash
pip install -e .
```

This will install the `ai-digest` command globally.

## Usage

### Basic Commands

```bash
# Display today's digest
ai-digest

# Display digest for a specific date
ai-digest --date 2025-01-23

# Display help
ai-digest --help
```

### Source Management

```bash
# List all sources with status
ai-digest sources list

# Add a custom RSS feed
ai-digest sources add --name "My AI Blog" --url https://myblog.com/feed.xml

# Add with a specific fetch method
ai-digest sources add --name "Custom API" --url https://api.example.com/articles --method api

# Remove a custom source
ai-digest sources remove my-ai-blog

# Disable/enable a source
ai-digest sources disable arxiv
ai-digest sources enable arxiv
```

Note: Built-in sources can be disabled but not removed.

### Podcast Summarization

Requires optional podcast dependencies:

```bash
pip install -e ".[podcast]"
```

```bash
# Summarize a podcast episode (default: base model)
ai-digest podcast https://www.latent.space/p/gpt5-analysis

# Use a faster model
ai-digest podcast https://example.com/episode.mp3 --model tiny

# Use a more accurate model
ai-digest podcast https://example.com/episode.mp3 --model small
```

**Model Selection**:

| Model | Speed | Accuracy | Best For |
|-------|-------|----------|----------|
| `tiny` | ~32x real-time | Basic | Quick checks |
| `base` | ~16x real-time | Good | Most podcasts (default) |
| `small` | ~6x real-time | Better | Important episodes |
| `medium` | ~2x real-time | Great | Maximum accuracy |

### Configuration

The tool uses a configuration file located at `~/.ai-digest/config.json` (created automatically on first run).

**Default Configuration**:

```json
{
  "sources": [...],
  "cache": {
    "directory": "~/.ai-digest/cache",
    "retention_days": 30
  },
  "fetch": {
    "freshness_hours": 48,
    "retry_count": 3,
    "retry_delays": [1, 2, 4]
  }
}
```

### Cache Location

- **Digests**: `~/.ai-digest/cache/digests/`
- **Articles**: `~/.ai-digest/cache/articles/`
- **Logs**: `~/.ai-digest/ai-digest.log`

Cached data is retained for 30 days by default.

## News Sources

The tool fetches from the following sources:

### Tech Platforms
- **HackerNews**: AI-related posts via Algolia API
- **Reddit**: r/MachineLearning top posts
- **ArXiv**: cs.AI, cs.LG, cs.CL categories

### AI Company Blogs
- OpenAI News
- Google DeepMind
- Anthropic Engineering
- Meta AI Research

### Thought Leaders
- Sam Schillace (Sunday Letters)
- Ethan Mollick (One Useful Thing)
- Andrew Ng (The Batch)

## Development

### Project Structure

```
src/
├── models/          # Data models (NewsArticle, Digest, etc.)
├── services/        # Business logic (fetcher, cache, summarizer)
│   └── fetchers/   # Source-specific fetchers
├── cli/            # CLI interface and formatting
└── config/         # Configuration loading and defaults

tests/
├── contract/       # CLI interface contract tests
├── integration/    # End-to-end tests
└── unit/          # Component-level tests
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code with ruff
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

## Troubleshooting

### No articles fetched

- Check your internet connection
- Some sources may be temporarily unavailable (tool handles this gracefully)
- Check logs at `~/.ai-digest/ai-digest.log` for details

### Cache issues

```bash
# Clear cache manually
rm -rf ~/.ai-digest/cache/

# Next run will fetch fresh data
ai-digest
```

### Invalid date format error

Make sure to use `YYYY-MM-DD` format:

```bash
# ✅ Correct
ai-digest --date 2025-01-23

# ❌ Wrong
ai-digest --date 01-23-2025
ai-digest --date 2025/01/23
```

## Performance

- **Fresh Fetch**: < 5 seconds (with retries)
- **Cached Digest**: < 1 second
- **100 Articles**: Processes in < 10 minutes

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please follow the existing code style and ensure all tests pass.

### Adding Custom Sources

Use the CLI to add custom sources:

```bash
ai-digest sources add --name "Custom AI Blog" --url https://example.com/feed.xml
```

## Architecture

The tool follows a modular architecture:

1. **Fetchers**: Source-specific adapters for HackerNews, Reddit, ArXiv, RSS
2. **Models**: Data validation and serialization
3. **Services**: Business logic (caching, retry, orchestration)
4. **CLI**: User interface and output formatting

## Success Criteria

- ✅ Digest retrieval < 5s (fresh), < 1s (cached)
- ✅ Articles from ≥ 5 different sources
- ✅ All articles have source attribution
- ✅ Handles up to 100 articles per day
- ✅ Graceful degradation with ≤ 50% source failures

## Support

For issues or questions, please check:

1. Logs at `~/.ai-digest/ai-digest.log`
2. Configuration at `~/.ai-digest/config.json`
3. GitHub Issues (if applicable)
