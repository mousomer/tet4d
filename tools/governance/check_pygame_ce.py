from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata


@dataclass(frozen=True)
class PygameRuntimeReport:
    pygame_ce_version: str | None
    pygame_version: str | None
    module_version: str | None
    module_path: str | None
    is_ce: bool
    issues: tuple[str, ...]


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def inspect_pygame_runtime() -> PygameRuntimeReport:
    pygame_ce_version = _dist_version("pygame-ce")
    pygame_version = _dist_version("pygame")

    module_version: str | None = None
    module_path: str | None = None
    is_ce = False
    issues: list[str] = []

    if pygame_ce_version is None:
        issues.append("Missing required package: pygame-ce")

    if pygame_version is not None:
        issues.append(
            "Legacy package detected: pygame. Uninstall it to avoid import shadowing."
        )

    try:
        import pygame
    except ModuleNotFoundError:
        issues.append("Unable to import pygame module.")
    else:
        module_version = str(getattr(pygame, "__version__", "unknown"))
        module_path = str(getattr(pygame, "__file__", "unknown"))
        is_ce = bool(getattr(pygame, "IS_CE", False))
        if not is_ce:
            issues.append(
                "Imported pygame module is not pygame-ce (pygame.IS_CE != True)."
            )

    return PygameRuntimeReport(
        pygame_ce_version=pygame_ce_version,
        pygame_version=pygame_version,
        module_version=module_version,
        module_path=module_path,
        is_ce=is_ce,
        issues=tuple(issues),
    )


def main() -> int:
    report = inspect_pygame_runtime()
    print(f"pygame-ce: {report.pygame_ce_version or 'missing'}")
    print(f"pygame: {report.pygame_version or 'not installed'}")
    print(f"pygame module version: {report.module_version or 'unavailable'}")
    print(f"pygame module path: {report.module_path or 'unavailable'}")
    print(f"pygame.IS_CE: {report.is_ce}")

    if report.issues:
        print("pygame runtime compatibility check failed:")
        for issue in report.issues:
            print(f"- {issue}")
        return 1

    print("pygame runtime compatibility check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
