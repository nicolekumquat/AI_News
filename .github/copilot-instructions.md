# Copilot Instructions for AI_News

## Git Push — Dual GitHub Account Setup

This repo (`nicolekumquat/AI_News`) requires pushing as the `nicolekumquat` account.
The developer's default/work account is `nical_microsoft`, which does NOT have push access.

**To push from this repo:**
1. `gh auth switch --user nicolekumquat`
2. `git push`
3. `gh auth switch --user nical_microsoft` (restore work account)

The local git config uses `gh auth git-credential` as the credential helper,
so pushes route through whichever `gh` account is currently active.
