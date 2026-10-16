"""Shared live language selection for the native application."""
import re
from .catalog import TRANSLATIONS, TEMPLATES


class Translator:
    def __init__(self, language="tr"):
        self.language = language if language in ("tr", "en") else "tr"
        self._bindings = []
        self._listeners = []

    def __call__(self, source, **values):
        source = {"balanced": "Dengeli", "performance": "Performans",
                  "power-saver": "Güç tasarrufu"}.get(source, source)
        if self.language == "en":
            result = TRANSLATIONS.get(source, source)
        else:
            result = next((tr for tr, en in TRANSLATIONS.items() if en == source), source)
        return result.format(**values) if values else result

    def dynamic(self, text):
        """Translate known UI text only, leaving diagnostic data untouched.

        Patterns are anchored whole sentences. Captured device names, paths and
        numbers are inserted literally, never evaluated or translated.
        """
        if not isinstance(text, str):
            return text
        exact = self(text)
        if exact != text:
            return exact
        for turkish, english in TEMPLATES:
            source, target = (turkish, english) if self.language == "en" else (english, turkish)
            names = re.findall(r"\{([a-z_]+)\}", source)
            if not names:
                continue
            pieces = re.split(r"\{[a-z_]+\}", source)
            pattern = "^" + "(.+?)".join(re.escape(piece) for piece in pieces) + "$"
            match = re.fullmatch(pattern, text, flags=re.DOTALL)
            if match:
                fields = dict(zip(names, match.groups()))
                # Nested known vocabulary, such as a D-pad direction, can be
                # translated; identifiers remain unchanged by exact lookup.
                fields = {name: self(value) if name in ("direction", "state", "access") else value
                          for name, value in fields.items()}
                return target.format(**fields)
        return text

    def bind(self, widget, source, setter="set_label"):
        self._bindings.append((widget, source, setter))
        getattr(widget, setter)(self(source))
        return widget

    def connect(self, callback):
        self._listeners.append(callback)

    def disconnect(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def set_language(self, language):
        if language not in ("tr", "en") or language == self.language:
            return
        self.language = language
        for widget, source, setter in self._bindings:
            getattr(widget, setter)(self(source))
        for callback in self._listeners:
            callback()
