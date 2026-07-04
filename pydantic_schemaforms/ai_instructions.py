from __future__ import annotations

from importlib import resources

_PROFILE_ALIASES: dict[str, str] = {
    'generic': 'generic',
    'default': 'generic',
    'copilot': 'copilot',
    'github-copilot': 'copilot',
    'claude': 'claude',
    'anthropic-claude': 'claude',
}

_PROFILE_TO_ASSET: dict[str, str] = {
    'generic': 'assets/ai/generic_app_instructions.md',
    'copilot': 'assets/ai/copilot_app_instructions.md',
    'claude': 'assets/ai/claude_app_instructions.md',
}


def available_instruction_profiles() -> tuple[str, ...]:
    """Return canonical app-integration instruction profiles bundled with the package."""
    return tuple(sorted(_PROFILE_TO_ASSET.keys()))


def suggested_instruction_filename(profile: str = 'generic') -> str:
    """Return a suggested filename for app repositories.

    This is only a recommendation and is not written automatically.
    """
    normalized = _normalize_profile(profile)
    if normalized == 'copilot':
        return '.github/copilot-instructions.md'
    if normalized == 'claude':
        return 'CLAUDE.md'
    return 'AI_INSTRUCTIONS.md'


def get_app_instructions(profile: str = 'generic') -> str:
    """Return packaged app-side integration instructions for an AI assistant profile.

    Profiles:
    - generic
    - copilot
    - claude

    Aliases are accepted (for example: github-copilot, anthropic-claude).
    """
    normalized = _normalize_profile(profile)
    relative_path = _PROFILE_TO_ASSET[normalized]
    package_root = resources.files('pydantic_schemaforms')
    return (package_root / relative_path).read_text(encoding='utf-8')


def _normalize_profile(profile: str) -> str:
    key = (profile or '').strip().lower()
    normalized = _PROFILE_ALIASES.get(key)
    if normalized:
        return normalized
    supported = ', '.join(available_instruction_profiles())
    raise ValueError(
        f'Unsupported instruction profile: {profile!r}. Supported profiles: {supported}'
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: print or write packaged AI-assistant instructions for an app repo.

    Examples::

        python -m pydantic_schemaforms.ai_instructions claude > CLAUDE.md
        python -m pydantic_schemaforms.ai_instructions copilot --write
    """
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog='python -m pydantic_schemaforms.ai_instructions',
        description='Print or write packaged AI-assistant instructions for app integrations.',
    )
    parser.add_argument(
        'profile',
        nargs='?',
        default='generic',
        help=f'Instruction profile (aliases accepted). One of: {", ".join(available_instruction_profiles())}.',
    )
    parser.add_argument(
        '--write',
        action='store_true',
        help='Write to the suggested destination file (e.g. CLAUDE.md) instead of stdout.',
    )
    parser.add_argument(
        '--output',
        metavar='PATH',
        help='Write to an explicit path instead of stdout or the suggested destination.',
    )
    args = parser.parse_args(argv)

    try:
        text = get_app_instructions(args.profile)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    destination = args.output or (
        suggested_instruction_filename(args.profile) if args.write else None
    )
    if destination is None:
        sys.stdout.write(text)
        return 0

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    print(f'Wrote {path}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
