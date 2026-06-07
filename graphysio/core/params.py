"""Declarative, Qt-free parameter schema shared by readers, desktop and web.

A reader describes the inputs it needs to load a file as a list of :class:`ParamSpec`
objects. The desktop renders them with Qt dialogs; the web serializes them to JSON
and renders a form. Neither the schema nor the readers import any GUI toolkit.

The flow is::

    while True:
        params = reader.get_params()   # may read the file to populate choices
        if not params:
            break                      # reader has everything it needs
        answers = ask(params)          # Qt dialog, web form, or defaults
        reader.set_data(answers)
    plotdata = reader()

``get_params`` is called repeatedly so a reader can ask in stages (e.g. iceberg
needs connection details before it can list a table's columns).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

__all__ = ["ParamKind", "ParamSpec", "default_answers", "gather"]

ParamKind = Literal[
    "int",
    "float",
    "str",
    "bool",
    "time",
    "datetime",
    "choice",
    "multichoice",
]


@dataclass
class ParamSpec:
    """One input a reader needs.

    Parameters
    ----------
    name:
        Key under which the answer is stored in the reader's ``userdata``.
    label:
        Human-readable prompt.
    kind:
        How to render/validate the input. ``"choice"`` is single-select and
        ``"multichoice"`` is multi-select over ``choices``; ``"time"`` is a duration
        string (e.g. ``"500ms"``) resolved to seconds by the renderer.
    choices:
        Allowed values for ``choice`` / ``multichoice``.
    default:
        Pre-filled value. For ``multichoice`` this is typically the full
        ``choices`` list (select everything).
    required:
        Whether an answer must be supplied.
    """

    name: str
    label: str
    kind: ParamKind
    choices: list[str] | None = None
    default: Any = None
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable form for the web frontend."""
        return {
            "name": self.name,
            "label": self.label,
            "kind": self.kind,
            "choices": self.choices,
            "default": self.default,
            "required": self.required,
        }


def default_answers(params: list[ParamSpec]) -> dict[str, Any]:
    """Answer every param with its ``default`` -- the headless/one-shot fallback.

    For ``multichoice`` with no explicit default, selects all choices, matching the
    desktop dialogs which pre-check every column.
    """
    answers: dict[str, Any] = {}
    for p in params:
        if p.default is not None:
            answers[p.name] = p.default
        elif p.kind == "multichoice":
            answers[p.name] = list(p.choices or [])
        else:
            answers[p.name] = None
    return answers


def gather(reader, ask: Callable[[list[ParamSpec]], dict[str, Any] | None]) -> bool:
    """Drive ``reader``'s staged ``get_params``/``set_data`` loop using ``ask``.

    ``ask`` receives the current params and returns an answers dict, or ``None`` to
    cancel. Returns ``True`` when the reader is fully configured, ``False`` if
    cancelled. The reader is not invoked here -- the caller calls ``reader()``.
    """
    while True:
        params = reader.get_params()
        if not params:
            return True
        answers = ask(params)
        if answers is None:
            return False
        reader.set_data(answers)
