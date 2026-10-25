# Mandatory Git Tracking & Configuration Preservation Rule (The Zero-Loss Invariant)

## 1. Mandatory Git Tracking on Every File Edit
- Whenever ANY configuration file, launcher script, application engine code, or template is modified or created, it MUST be staged and committed to Git immediately.
- NEVER leave working configs, tuned parameters, or engine fixes as untracked files or ignored in `.gitignore`.
- All critical runtime configurations MUST have an authoritative, version-controlled copy in the dedicated `CONFIG/` directory (`CONFIG/stage_1_audio/`, `CONFIG/stage_2_screen/`).

## 2. Pre-Clean & Refactoring Safety Gate
- NEVER reorganize directories, archive folders, or delete files without first running `git status` and verifying that all active configurations, custom UI styles, and model tuning parameters are safely committed and mirrored in `CONFIG/`.
- If any file is excluded by `.gitignore` in upstream submodules (e.g., `user_settings.json`), it must either be explicitly un-ignored or tracked via `CONFIG/` so that no user settings can ever be lost during cleanups.
