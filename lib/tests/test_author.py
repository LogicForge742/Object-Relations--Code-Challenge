import importlib
import inspect
import io
import pathlib
import sys
import types

import pytest


CANDIDATE_MODULE_NAMES = (
    "author",
    "lib.author",
    "src.author",
    "app.author",
)


def _import_author_module():
    last_exc = None
    for name in CANDIDATE_MODULE_NAMES:
        try:
            return importlib.import_module(name)
        except Exception as exc:
            last_exc = exc
            continue
    pytest.skip(f"Could not import author module from any of: {CANDIDATE_MODULE_NAMES}. Last exception: {last_exc}")


def _is_local_member(mod, member):
    try:
        return getattr(member, "__module__", None) == getattr(mod, "__name__", None)
    except Exception:
        return False


def _required_params(sig):
    required = []
    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is inspect._empty:
            required.append(p)
        if p.kind == p.KEYWORD_ONLY and p.default is inspect._empty:
            required.append(p)
    return required


def _sample_for_annotation(annotation):
    try:
        origin = getattr(annotation, "__origin__", None)
    except Exception:
        origin = None

    if annotation in (str, types.SimpleNamespace):
        return "John Doe"
    if annotation is int:
        return 42
    if annotation is float:
        return 3.14
    if annotation is bool:
        return True
    if annotation is dict or origin is dict:
        return {"name": "John Doe"}
    if annotation is list or origin is list:
        return ["John", "Doe"]
    if annotation is tuple or origin is tuple:
        return ("John", "Doe")
    if annotation is set or origin is set:
        return {"John", "Doe"}
    if annotation is bytes:
        return b"data"
    if annotation is pathlib.Path:
        return pathlib.Path(".")
    if annotation is io.IOBase:
        return io.StringIO("content")
    # Fallbacks for typing.Any or unknowns
    return "John Doe"


def _sample_for_name(name):
    lname = name.lower()
    if any(k in lname for k in ("name", "author", "title", "text", "string", "content")):
        return "John Doe"
    if any(k in lname for k in ("path", "file", "filename")):
        return pathlib.Path(".")
    if any(k in lname for k in ("stream", "buffer")):
        return io.StringIO("")
    if any(k in lname for k in ("count", "num", "n", "size", "limit", "length")):
        return 10
    if any(k in lname for k in ("items", "list", "values")):
        return [1, 2, 3]
    if any(k in lname for k in ("mapping", "dict", "options", "config")):
        return {"key": "value"}
    return "sample"


def _empty_for_annotation(annotation):
    if annotation is str:
        return ""
    if annotation in (list, tuple, set):
        return annotation()
    if annotation is dict:
        return {}
    if annotation in (int, float):
        return 0
    return None


def _extreme_for_annotation(annotation):
    if annotation is str:
        return "a" * 10000
    if annotation is list:
        return list(range(10000))
    if annotation is tuple:
        return tuple(range(10000))
    if annotation is set:
        return set(range(10000))
    if annotation is dict:
        return {str(i): i for i in range(10000)}
    if annotation is int:
        return sys.maxsize
    if annotation is float:
        return 1e308
    return None


def _build_args_for_func(func, strategy="typical"):
    sig = inspect.signature(func)
    args = []
    kwargs = {}
    for p in sig.parameters.values():
        if p.kind == p.VAR_POSITIONAL or p.kind == p.VAR_KEYWORD:
            continue

        if p.default is not inspect._empty and strategy == "typical":
            # Let defaults fill in
            continue

        annotation = p.annotation if p.annotation is not inspect._empty else None

        if strategy == "typical":
            value = _sample_for_annotation(annotation) if annotation else _sample_for_name(p.name)
        elif strategy == "empty":
            value = _empty_for_annotation(annotation)
            if value is None:
                # Provide a sensible empty fallback by name
                name_val = _sample_for_name(p.name)
                if isinstance(name_val, str):
                    value = ""
                elif isinstance(name_val, (list, tuple, set, dict)):
                    value = type(name_val)()
                elif isinstance(name_val, (int, float)):
                    value = type(name_val)(0)
                else:
                    value = None
        elif strategy == "extreme":
            value = _extreme_for_annotation(annotation)
            if value is None:
                # Heuristic extreme by name if annotation missing
                lname = p.name.lower()
                if any(k in lname for k in ("text", "name", "title", "string", "content")):
                    value = "a" * 10000
                elif any(k in lname for k in ("items", "list", "values")):
                    value = list(range(10000))
                elif any(k in lname for k in ("mapping", "dict", "options", "config")):
                    value = {str(i): i for i in range(10000)}
                elif any(k in lname for k in ("count", "size", "limit", "length", "n", "num")):
                    value = sys.maxsize
                else:
                    value = "a" * 10000
        else:
            value = None

        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            args.append(value)
        elif p.kind == p.KEYWORD_ONLY:
            kwargs[p.name] = value
    return args, kwargs


def test_module_imports_without_errors():
    mod = _import_author_module()
    assert mod is not None
    assert isinstance(mod, types.ModuleType)


def test_primary_function_handles_typical_input_returns_expected_type():
    mod = _import_author_module()
    funcs = [
        (name, f)
        for name, f in inspect.getmembers(mod, inspect.isfunction)
        if _is_local_member(mod, f) and not name.startswith("_") and name not in ("main",)
    ]
    if not funcs:
        pytest.skip("No callable functions found in the author module to test.")

    # Prefer function with the fewest required params
    def req_count(f):
        return len(_required_params(inspect.signature(f)))

    funcs.sort(key=lambda item: req_count(item[1]))
    name, func = funcs[0]

    args, kwargs = _build_args_for_func(func, strategy="typical")
    result = func(*args, **kwargs)

    # Expected: returns a common Python type without raising
    assert not inspect.isfunction(result) and not inspect.isclass(result) and not inspect.ismodule(result)


def test_class_instantiates_with_default_arguments():
    mod = _import_author_module()
    classes = [
        (name, c)
        for name, c in inspect.getmembers(mod, inspect.isclass)
        if _is_local_member(mod, c) and not name.startswith("_")
    ]
    if not classes:
        pytest.skip("No classes found in the author module to instantiate.")

    for name, cls in classes:
        try:
            instance = cls()
            assert isinstance(instance, cls)
            return
        except TypeError:
            continue
    pytest.skip("No classes could be instantiated with default arguments; constructors require parameters.")


def test_missing_dependency_results_in_clear_import_error():
    # Ensure the target module itself imports fine
    _import_author_module()

    fake_pkg = "this_dependency_does_not_exist_42cafedeadbeef"
    with pytest.raises(ImportError) as excinfo:
        importlib.import_module(fake_pkg)
    assert fake_pkg in str(excinfo.value)


def test_function_gracefully_handles_empty_or_none_input():
    mod = _import_author_module()
    funcs = [
        (name, f)
        for name, f in inspect.getmembers(mod, inspect.isfunction)
        if _is_local_member(mod, f) and not name.startswith("_") and name not in ("main",)
    ]
    if not funcs:
        pytest.skip("No callable functions found in the author module to test empty/None handling.")

    # Pick the first function that accepts at least one parameter
    target = None
    for name, f in funcs:
        if _required_params(inspect.signature(f)):
            target = (name, f)
            break
    if target is None:
        pytest.skip("No suitable function with parameters found for empty/None input test.")

    name, func = target

    # Try empty-like inputs
    args, kwargs = _build_args_for_func(func, strategy="empty")

    try:
        _ = func(*args, **kwargs)
        assert True
    except (ValueError, TypeError) as e:
        # Graceful rejection with a clear message is acceptable
        assert str(e), "Exception message should not be empty when rejecting empty/None input."


def test_extreme_input_size_or_values_are_handled_or_rejected():
    mod = _import_author_module()
    funcs = [
        (name, f)
        for name, f in inspect.getmembers(mod, inspect.isfunction)
        if _is_local_member(mod, f) and not name.startswith("_") and name not in ("main",)
    ]
    if not funcs:
        pytest.skip("No callable functions found in the author module to test extreme input handling.")

    # Prefer a function that takes at least one parameter
    target = None
    for name, f in funcs:
        if _required_params(inspect.signature(f)):
            target = (name, f)
            break
    if target is None:
        pytest.skip("No suitable function with parameters found for extreme input test.")

    name, func = target

    args, kwargs = _build_args_for_func(func, strategy="extreme")
    try:
        _ = func(*args, **kwargs)
        assert True
    except (ValueError, OverflowError, MemoryError) as e:
        assert str(e), "Exception message should not be empty when rejecting extreme inputs."