# Feature Specification: Daily News Aggregation

**Feature Branch**: `001-daily-news-aggregation`  
**Created**: 2025-01-23  
**Status**: Draft  
**Input**: User description: "Create a feature specification for the daily news aggregation feature of the AI Daily Digest project. Context from the constitution (.specify/memory/constitution.md): - Project: AI Daily Digest - aggregates AI news into small consumable chunks as a daily update - Core Principles: Content-First, Test-First (TDD), Simplicity - Tech Stack: Python 3.11+, pytest, ruff, local deployment only - Content & Data Standards: source attribution required, deduplication mandatory, 48-hour freshness window, summaries must be transformed (not raw), local caching required The feature should cover: fetching AI news from sources, summarizing/condensing articles into digestible chunks, deduplicating content, and presenting a daily digest to the user."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Daily AI News Digest (Priority: P1)

As a user, I want to receive a daily digest of AI news so that I can stay informed about the latest developments in AI without spending hours reading multiple sources.

**Why this priority**: This is the core value proposition of the entire feature - delivering curated AI news to users. Without this, the feature has no value to deliver.

**Independent Test**: Can be fully tested by requesting a digest for a specific date and verifying that relevant AI news articles are returned in a condensed, readable format. Delivers immediate value by providing users with curated AI news.

**Acceptance Scenarios**:

1. **Given** the system has fetched and processed AI news articles, **When** a user requests today's digest, **Then** they receive a formatted list of AI news summaries with source attribution
2. **Given** multiple news articles from different sources exist, **When** a user requests the digest, **Then** the digest contains articles from multiple sources without duplicates
3. **Given** no new articles are available within the 48-hour window, **When** a user requests the digest, **Then** they receive a message indicating no new content is available
4. **Given** articles are available in the cache, **When** a user requests the digest for a date already processed, **Then** the cached digest is returned without re-fetching sources

---

### User Story 2 - Automatic News Source Fetching (Priority: P1)

As a system, I need to automatically fetch AI news from configured sources so that the digest always contains fresh, relevant content for users.

**Why this priority**: This is the foundation of content delivery. Without automatic fetching, there is no content to aggregate and present to users. This is equally critical as the presentation layer.

**Independent Test**: Can be tested by configuring news sources, triggering a fetch operation, and verifying that articles are retrieved and stored. Delivers value by ensuring the system has fresh content to work with.

**Acceptance Scenarios**:

1. **Given** news sources are configured, **When** the fetch process runs, **Then** articles published within the last 48 hours are retrieved from all sources
2. **Given** a news source is temporarily unavailable, **When** the fetch process runs, **Then** the system continues to fetch from available sources without failing completely
3. **Given** articles have already been fetched, **When** the fetch process runs again, **Then** only new articles since the last fetch are retrieved
4. **Given** a source returns an error or invalid data, **When** the fetch process runs, **Then** the error is logged and the system continues processing other sources

---

### User Story 3 - Content Deduplication (Priority: P2)

As a user, I want to see each unique AI news story only once in my digest so that I don't waste time reading the same information from multiple sources.

**Why this priority**: This significantly improves user experience by removing redundancy, but the system can still deliver value with duplicates (users can manually skip them). It's important but not blocking for MVP.

**Independent Test**: Can be tested by feeding the system multiple articles covering the same story from different sources and verifying only one version appears in the digest. Delivers value by improving content quality and readability.

**Acceptance Scenarios**:

1. **Given** multiple sources report the same AI news story, **When** the deduplication process runs, **Then** only one version of the story appears in the digest
2. **Given** two articles share some keywords but cover different aspects of AI, **When** deduplication runs, **Then** both articles are retained as they provide unique value
3. **Given** an article is a near-duplicate with minor wording changes, **When** deduplication runs, **Then** the system identifies and removes the duplicate
4. **Given** articles from the same source with identical titles, **When** deduplication runs, **Then** duplicates are removed even from the same source

---

### User Story 4 - Content Summarization (Priority: P2)

As a user, I want articles condensed into digestible summaries so that I can quickly understand key points without reading full-length articles.

**Why this priority**: This enhances the user experience by making content more consumable, but users can still derive value from article titles and links to full content. It's a quality enhancement rather than a functional requirement.

**Independent Test**: Can be tested by providing full-length articles and verifying that transformed summaries are generated that capture key points in fewer words. Delivers value by reducing reading time.

**Acceptance Scenarios**:

1. **Given** a full-length article, **When** the summarization process runs, **Then** a condensed summary is generated that captures the main points
2. **Given** an article with technical AI terminology, **When** summarization occurs, **Then** key technical terms and concepts are preserved in the summary
3. **Given** articles of varying lengths, **When** summarization runs, **Then** summaries are relatively consistent in length (not just proportional reductions)
4. **Given** an article has already been summarized, **When** the same article is processed again, **Then** the cached summary is used rather than re-processing

---

### User Story 5 - Manual Digest Refresh (Priority: P3)

As a user, I want to manually refresh my digest to check for new articles so that I can get updates throughout the day rather than waiting for the next scheduled update.

**Why this priority**: This is a convenience feature that improves user experience but is not essential for the core daily digest functionality. Users can wait for the next scheduled update.

**Independent Test**: Can be tested by manually triggering a refresh and verifying that any new articles published since the last fetch are included in an updated digest. Delivers value by giving users control over content freshness.

**Acceptance Scenarios**:

1. **Given** new articles have been published since the last scheduled fetch, **When** a user requests a manual refresh, **Then** the new articles are fetched and included in an updated digest
2. **Given** no new articles are available, **When** a user requests a manual refresh, **Then** the system indicates the digest is already up-to-date
3. **Given** a manual refresh is in progress, **When** another refresh request is made, **Then** the system queues or rejects the second request rather than processing both simultaneously

---

### Edge Cases & Failure Handling

**Source Availability & Fetch Failures**
- **All sources unavailable**: System MUST generate an empty digest with a clear message indicating no sources were accessible, including timestamp of last successful fetch attempt
- **Rate limiting or access restrictions**: System applies the standard retry mechanism (3 attempts with exponential backoff: 1s, 2s, 4s). If rate limit persists, the source is skipped for the current digest cycle and logged for monitoring
- **Source returns malformed data**: System logs the parsing error with source details, skips that specific article/feed, and continues processing remaining content from that source and other sources

**Article Metadata & Content Issues**
- **Missing or incomplete article metadata** (title, date, source): System MUST reject articles lacking title or source attribution; publication date defaults to fetch timestamp if missing with a warning logged
- **Articles with missing source attribution**: Rejected and not included in the digest; logged as a data quality issue for investigation
- **Extremely long articles** (>10,000 words): Summarization process applies a maximum content length limit of 10,000 words; content beyond this is truncated before summarization
- **Extremely short articles** (<50 words): Included without summarization; original text is used as the summary since reduction wouldn't provide value
- **Articles in non-English languages**: Out of scope for MVP; non-English articles are filtered out during processing based on language detection heuristics

**Processing & Data Integrity Failures**
- **Summarization failure for a specific article**: System logs the error, falls back to using the first 2-3 sentences of the article as a summary, and includes the article in the digest with a flag indicating fallback mode
- **Deduplication process failure**: System logs a critical error and continues to generate the digest without deduplication; duplicates may appear but content is still delivered; monitoring alert is triggered
- **Cache corruption or unavailability**: System detects corruption on read, logs error, invalidates the corrupted cache entry, and re-fetches/re-processes the affected content; digest generation continues with fresh data
- **Very old articles passing 48-hour filter** (timestamp inconsistencies): System applies a secondary validation check rejecting articles with publication dates >72 hours old (allowing for timezone variations and clock skew)

**Volume & Performance Edge Cases**
- **Article volume exceeds 100 per day**: System processes all articles but prioritizes by source diversity and recency, presenting the top 100 articles in the digest; overflow articles are cached but not displayed
- **Concurrent digest requests**: System uses file-based locking to prevent simultaneous processing; if a digest is being generated, subsequent requests wait (with timeout) or return the last completed digest if available

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch articles from configured news sources at scheduled intervals
- **FR-002**: System MUST filter articles to include only those published within the last 48 hours
- **FR-003**: System MUST attribute each article to its original source with source name and publication date
- **FR-004**: System MUST deduplicate articles to ensure each unique story appears only once in the digest. Deduplication MUST use combined title + content similarity analysis with keyword overlap or simple cosine similarity, applying a 75% match threshold to identify duplicates
- **FR-005**: System MUST transform/summarize article content rather than presenting raw article text
- **FR-006**: System MUST cache fetched and processed articles locally to reduce redundant processing
- **FR-007**: System MUST present the digest in a readable format with clear separation between articles
- **FR-008**: Users MUST be able to request a digest for the current day via command: `ai-digest` (default: today)
- **FR-008a**: Users MUST be able to request a digest for a specific date via command: `ai-digest --date YYYY-MM-DD`
- **FR-008b**: System MUST support configuration via JSON or YAML config file for options beyond date selection (e.g., source configuration, cache location, summarization parameters)
- **FR-009**: System MUST handle individual source failures gracefully without preventing digest generation from available sources. When a source fetch fails, the system MUST retry up to 3 times with exponential backoff delays (1 second, 2 seconds, 4 seconds). After exhausting retries, the system MUST log the failure and continue processing remaining sources.
- **FR-010**: System MUST log all fetch operations, errors, and processing steps for debugging and monitoring
- **FR-011**: System MUST validate that summaries are transformations and not direct copies of source content
- **FR-012**: System MUST persist deduplication decisions to avoid re-processing the same duplicates
- **FR-013**: System MUST be capable of processing and presenting up to 100 articles per daily digest to provide comprehensive coverage of AI news

### Key Entities *(include if feature involves data)*

- **NewsArticle**: Represents a fetched article with attributes including title, source name, publication date, original content URL, raw content, processed summary, fetch timestamp, and unique identifier
- **NewsSource**: Represents a configured source for fetching AI news. Sources include: HackerNews AI filter, Reddit r/MachineLearning, ArXiv AI papers, and blogs from AI thought leaders (Sam Schillace, Ethan Mollick, Andrew Ng, OpenAI leadership, Anthropic leadership, Google DeepMind leadership, Meta AI leadership). Attributes: source name, fetch URL/endpoint, fetch method, last successful fetch timestamp, and enabled/disabled status
- **DigestEntry**: Represents a processed article ready for inclusion in the digest, including article reference, summary text, source attribution, publication date, and inclusion timestamp
- **Digest**: Represents a daily collection of DigestEntry items for a specific date, including creation timestamp, article count, and cache status

### Assumptions

- News sources will provide articles in a parseable format (HTML, RSS, JSON, etc.)
- AI news is primarily in English language
- Users access the digest through a command-line interface: `ai-digest [--date YYYY-MM-DD]` where date defaults to today
- System configuration (sources, cache location, processing options) is managed via a JSON or YAML configuration file rather than command-line flags
- Summarization can be achieved through simple text processing techniques (extractive summarization) without requiring external AI services
- Deduplication uses combined title + content similarity with keyword overlap or simple cosine similarity (75% match threshold)
- The 48-hour freshness window is sufficient to capture relevant daily AI news
- Local storage (filesystem) is sufficient for caching needs with capacity for at least 30 days of cached digests (approximately 3,000 articles)
- News sources do not require authentication or complex API integration (for MVP scope)
- Article volume under normal operation will not exceed 100 articles per day per the comprehensive coverage target
- System will operate on a single machine without distributed processing requirements
- Language detection heuristics (e.g., character set analysis, common English words) are sufficient to filter non-English content

## Clarifications

### Session 2025-01-23

- Q: Which specific news sources should the system aggregate from? → A: Use the 3 suggested sources (HackerNews AI filter, Reddit r/MachineLearning, ArXiv AI papers) PLUS blogs from AI thought leaders: Sam Schillace's blog, Ethan Mollick's blog, Andrew Ng's content, and other leaders of major AI companies (e.g., OpenAI, Anthropic, Google DeepMind, Meta AI leadership blogs/newsletters)
- Q: How should users interact with the system: through environment flags/CLI, API endpoints, config file, or other interface? → A: Simple single command with date parameter: `ai-digest [--date YYYY-MM-DD]` (default: today), other options via JSON/YAML config file
- Q: When a news source fetch fails, should the system: A) Fail the entire digest generation, B) Limited retries with exponential backoff, C) Continue without retries and just log the failure, or D) Queue for later retry and continue? → A: Limited retries with exponential backoff. Retry each failed source up to 3 times with increasing delays (1s, 2s, 4s). After exhausting retries, log failure and continue with remaining sources.
- Q: What deduplication algorithm should be used to identify duplicate articles? → A: Combined title + content similarity using keyword overlap or simple cosine similarity with a 75% match threshold to identify duplicates.
- Q: What is the target volume of articles per day the system should handle? → A: Up to 100 articles per day (comprehensive coverage)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a daily digest containing AI news articles in under 5 seconds from request time
- **SC-002**: The digest contains articles from at least 5 different sources when available (covering HackerNews, Reddit, ArXiv, and thought leader blogs)
- **SC-003**: Duplicate articles are reduced by at least 90% compared to raw fetched content
- **SC-004**: Article summaries are at least 50% shorter than original content while retaining key information
- **SC-005**: The system successfully generates a digest even when up to 50% of configured sources are unavailable
- **SC-006**: All articles in the digest include complete source attribution (source name and publication date)
- **SC-007**: Cached digests are retrieved in under 1 second
- **SC-008**: The system processes new articles and updates the digest within 10 minutes of fetching
- **SC-009**: Zero raw/untransformed article content appears in the digest output
- **SC-010**: The system successfully processes and presents up to 100 articles in a single digest without performance degradation
- **SC-011**: Articles with missing critical metadata (title or source) are rejected with a rejection rate logged in system metrics
- **SC-012**: When summarization fails, fallback summaries (first 2-3 sentences) are used successfully in 100% of failure cases
