"""L0 — 엔진 공통 예외. 메시지는 사용자에게 그대로 노출된다."""


class AutodocsError(Exception):
    """엔진이 의도적으로 중단할 때 발생. CLI 는 exit code 2 로 매핑."""


class StandardNotFound(AutodocsError):
    pass


class ProfileInvalid(AutodocsError):
    pass
