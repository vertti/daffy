import pytest

from daffy.utils import ParameterResolver


def test_resolver_default_kwargs() -> None:
    def func(a: int, *, b: int = 10) -> None:
        pass

    resolver = ParameterResolver(func)

    # Missing optional kwarg
    val, _ = resolver.resolve("b", 1)
    assert val == 10

    # Missing required kwarg
    def func_req(a: int, *, b: int) -> None:
        pass

    resolver_req = ParameterResolver(func_req)
    with pytest.raises(ValueError, match="Required keyword-only parameter"):
        resolver_req.resolve("b", 1)


def test_resolver_default_pos() -> None:
    def func(a: int, b: int = 20) -> None:
        pass

    resolver = ParameterResolver(func)

    # Missing optional pos arg
    val, _ = resolver.resolve("b", 1)
    assert val == 20
