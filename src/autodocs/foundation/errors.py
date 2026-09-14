"""L0 — 엔진 공통 예외. 메시지는 사용자에게 그대로 노출된다.

CLI 는 AutodocsError(및 그 하위) 를 exit 2 로 매핑한다. 그 외 예외도 exit 2 이지만 트레이스백을 낸다.
"""


class AutodocsError(Exception):
    """엔진이 의도적으로 중단할 때 발생."""


class StandardNotFound(AutodocsError):
    pass


class ManifestInvalid(AutodocsError):
    pass


class ProfileInvalid(AutodocsError):
    pass


class PathEscape(AutodocsError):
    """root(또는 standard dir) 밖을 가리킬 수 있는 경로 입력. 출처(manifest/profile/CLI)를 불문하고 거부."""
