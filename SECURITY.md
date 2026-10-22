# Security

Vellum is a local Claude Code plugin. It does not run a service, does not send
telemetry, and does not make network requests of its own. This document states
plainly what it touches, what it does not, and how to report a problem.

## What the plugin executes

- **Hook scripts** in `hooks/scripts/` run under the bash bundled with Git for
  Windows (or the system bash elsewhere). They read the hook payload Claude Code
  sends on stdin, inspect file paths and session context, and may block a tool
  call by exiting 2. The blocking gate is intentionally narrow: unapproved
  writes into `manuscript/chapters/`.
- **The Python engine** (`scripts/vellum`, `scripts/vellum_lib/`) runs only when
  a hook or a command invokes it. It is standard-library Python ≥ 3.8 and does
  not install packages at runtime. `project-setup` copies the engine into your
  novel project; the copy is the same code.
- **The series CLI** (`scripts/library.py`) runs only when you or an agent invoke
  a `library` subcommand. It operates on an explicit `--root` directory.

## What it reads and writes

- Your novel project: `manuscript/`, `kb/`, `state/`, `work/`, and `export/`.
- The plugin's own files, read-only.
- State left by Claude Code itself, only where documented (for example, locating
  session transcripts to verify a gate artifact's provenance).

It does not read unrelated directories, browser data, credentials, or
environment secrets. It does not upload manuscript content anywhere. Your
manuscript remains your repository; Vellum never commits, pushes, or rewrites
prose.

## Trust boundaries worth knowing

- **Agent permissions are part of the design.** Critics and readers are
  read-only by frontmatter; the writer's write scope is `manuscript/` and
  `work/drafts/`. These are harness-enforced permissions, not prompt requests.
- **Gate artifacts are files on disk.** Do not treat a chat claim as evidence.
  The engine verifies the artifact and, where available, a provenance run stamp.
- **Hooks fail open on missing infrastructure.** If no Python interpreter
  resolves, engine-dependent preconditions skip with an advisory rather than
  blocking you. Gate-input protection is the deliberate exception: it fails
  closed when session context cannot be verified.
- **You can inspect everything.** Hook scripts, engine modules, and the site
  build script are plain text in this repository. There is no compiled binary
  and no hidden service.

## Supported versions

Security fixes are made on `main` and released in the latest version. The plugin
currently has no LTS branch; pin a commit or release tag if you need stability.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's
private vulnerability reporting on this repository
(<https://github.com/FiredMosquito831/my-writing-companion/security/advisories/new>)
or contact the maintainer, [FiredMosquito831](https://github.com/FiredMosquito831),
through GitHub. Include the affected version, a minimal reproduction, and the
impact you believe it has. You can expect an acknowledgement within a reasonable
period; please allow time for a fix before public disclosure.

## Scope

In scope: the plugin's hook scripts, Python engine, agents, skills, commands,
templates, and the generated site's build script.

Out of scope: vulnerabilities in Claude Code itself, in Git or Python, or in
third-party tools you choose to install (Pandoc, for example), and findings that
require an attacker to already control your local files or your Claude Code
configuration.
