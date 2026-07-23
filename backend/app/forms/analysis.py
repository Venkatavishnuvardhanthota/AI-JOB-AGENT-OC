from __future__ import annotations

import uuid
from typing import Any

from app.forms.classification import FieldClassifier
from app.forms.schemas import (
    FieldState,
    FieldType,
    FormAnalysisResult,
    FormField,
)


class FormAnalyzer:
    def __init__(self, classifier: FieldClassifier | None = None) -> None:
        self._classifier = classifier or FieldClassifier()

    def analyze(self, page: Any, url: str) -> FormAnalysisResult:
        fields = self.extract_fields(page)
        result = FormAnalysisResult(url=url, fields=fields, total_fields=len(fields))

        for field in fields:
            classification = self._classifier.classify(field)
            result.classifications.append(classification)

        result.classified_count = len(result.classifications)
        return result

    def extract_fields(self, page: Any) -> list[FormField]:
        fields: list[FormField] = []
        elements = self._query_form_elements(page)
        seen_selectors: set[str] = set()

        for element in elements:
            selector = self._build_selector(element)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)

            field = self._extract_field(element)
            if field:
                fields.append(field)

        return fields

    def _query_form_elements(self, page: Any) -> list[Any]:
        elements: list[Any] = []
        selectors = [
            "input:not([type='submit']):not([type='button']):not([type='reset']):not([type='image'])",
            "select",
            "textarea",
        ]
        for sel in selectors:
            try:
                found = page.query_selector_all(sel)
                elements.extend(found)
            except Exception:
                pass
        return elements

    def _extract_field(self, element: Any) -> FormField | None:
        try:
            tag = (element.evaluate("el => el.tagName") or "input").lower()
        except Exception:
            tag = "input"

        field_type_str = self._get_attr(element, "type") or "text"
        field_type = self._to_field_type(tag, field_type_str)
        if field_type == FieldType.HIDDEN:
            return None

        field_id = self._get_attr(element, "id") or str(uuid.uuid4())
        name = self._get_attr(element, "name")
        selector = self._build_element_selector(tag, field_id, name)

        placeholder = self._get_attr(element, "placeholder")
        autocomplete = self._get_attr(element, "autocomplete")
        required = self._is_required(element)
        readonly = self._is_readonly(element)
        disabled = self._is_disabled(element)
        visible = self._is_visible(element)

        label = self._extract_label(element, field_id)
        description = self._extract_description(element, field_id)
        group = self._extract_group(element)

        options: list[str] = []
        if tag == "select":
            options = self._extract_options(element)

        return FormField(
            id=field_id,
            selector=selector,
            field_type=field_type,
            state=FieldState(
                required=required,
                readonly=readonly,
                disabled=disabled,
                visible=visible,
            ),
            label=label,
            placeholder=placeholder or None,
            description=description,
            group=group,
            autocomplete=autocomplete or None,
            options=options,
            name=name or None,
            tag_name=tag,
        )

    def _get_attr(self, element: Any, attr: str) -> str | None:
        try:
            return element.get_attribute(attr)
        except Exception:
            return None

    def _to_field_type(self, tag: str, type_str: str) -> FieldType:
        if tag == "select":
            return FieldType.SELECT
        if tag == "textarea":
            return FieldType.TEXTAREA
        type_map: dict[str, FieldType] = {
            "text": FieldType.TEXT,
            "email": FieldType.EMAIL,
            "tel": FieldType.PHONE,
            "number": FieldType.NUMBER,
            "url": FieldType.URL,
            "password": FieldType.TEXT,
            "search": FieldType.TEXT,
            "file": FieldType.FILE,
            "checkbox": FieldType.CHECKBOX,
            "radio": FieldType.RADIO,
            "date": FieldType.DATE,
            "datetime-local": FieldType.DATE,
            "month": FieldType.DATE,
            "week": FieldType.DATE,
            "time": FieldType.DATE,
            "hidden": FieldType.HIDDEN,
        }
        return type_map.get(type_str, FieldType.TEXT)

    def _is_required(self, element: Any) -> bool:
        try:
            return bool(element.get_attribute("required")) or bool(
                element.evaluate("el => el.required")
            )
        except Exception:
            return False

    def _is_readonly(self, element: Any) -> bool:
        try:
            return bool(element.get_attribute("readonly")) or bool(
                element.evaluate("el => el.readOnly")
            )
        except Exception:
            return False

    def _is_disabled(self, element: Any) -> bool:
        try:
            return bool(element.get_attribute("disabled")) or bool(
                element.evaluate("el => el.disabled")
            )
        except Exception:
            return False

    def _is_visible(self, element: Any) -> bool:
        try:
            return bool(element.evaluate(
                "el => el.offsetParent !== null && !el.hidden && el.type !== 'hidden'"
            ))
        except Exception:
            return True

    def _extract_label(self, element: Any, field_id: str) -> str | None:
        candidates: list[str] = []

        try:
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                candidates.append(aria_label)
        except Exception:
            pass

        try:
            aria_labelledby = element.get_attribute("aria-labelledby")
            if aria_labelledby:
                label_text = element.evaluate(
                    "el => { const id = arguments[0]; const ref = document.getElementById(id);"
                    " return ref ? ref.textContent.trim() : null; }",
                    aria_labelledby,
                )
                if label_text:
                    candidates.append(str(label_text))
        except Exception:
            pass

        if field_id and field_id != str(uuid.uuid4()):
            try:
                label_text = element.evaluate(
                    "el => { const id = arguments[0]; const f = `label[for=\"${id}\"]`;"
                    " const label = document.querySelector(f); return label ? label.textContent.trim() : null; }",
                    field_id,
                )
                if label_text:
                    candidates.append(str(label_text))
            except Exception:
                pass

        try:
            parent_label = element.evaluate(
                "el => { const p = el.closest('label'); return p ? p.textContent.trim() : null; }"
            )
            if parent_label:
                parent_text = str(parent_label)
                input_text = element.evaluate("el => el.value || el.placeholder || ''") or ""
                if input_text and isinstance(input_text, str):
                    parent_text = parent_text.replace(input_text, "").strip()
                if parent_text:
                    candidates.append(parent_text)
        except Exception:
            pass

        try:
            placeholder = element.get_attribute("placeholder")
            if placeholder:
                candidates.append(placeholder)
        except Exception:
            pass

        for c in candidates:
            if c and len(c) < 200:
                return c.strip()

        return None

    def _extract_description(self, element: Any, field_id: str) -> str | None:
        try:
            describedby = element.get_attribute("aria-describedby")
            if describedby:
                desc = element.evaluate(
                    "el => { const id = arguments[0]; const ref = document.getElementById(id);"
                    " return ref ? ref.textContent.trim() : null; }",
                    describedby,
                )
                if desc:
                    return str(desc)
        except Exception:
            pass
        return None

    def _extract_group(self, element: Any) -> str | None:
        try:
            group = element.evaluate(
                "el => { const fs = el.closest('fieldset');"
                " if (fs) { const legend = fs.querySelector('legend');"
                " return legend ? legend.textContent.trim() : null; } return null; }"
            )
            if group:
                return str(group)
        except Exception:
            pass
        return None

    def _extract_options(self, element: Any) -> list[str]:
        options: list[str] = []
        try:
            opt_elements = element.query_selector_all("option")
            for opt in opt_elements:
                try:
                    text = opt.text_content()
                    if text:
                        options.append(text.strip())
                except Exception:
                    pass
        except Exception:
            pass
        return options

    def _build_selector(self, element: Any) -> str:
        try:
            tag = (element.evaluate("el => el.tagName") or "input").lower()
            field_id = element.get_attribute("id")
            name = element.get_attribute("name")
            class_name = element.get_attribute("class")
            idx = element.evaluate(
                "el => { const same = document.querySelectorAll(el.tagName); return Array.from(same).indexOf(el); }"
            )
            if field_id:
                return f"#{field_id}"
            if name:
                return f"{tag}[name='{name}']"
            if class_name:
                cls = class_name.strip().split()[0]
                return f"{tag}.{cls}"
            return f"{tag}:nth-of-type({idx + 1})"
        except Exception:
            return "unknown"

    def _build_element_selector(self, tag: str, field_id: str, name: str | None) -> str:
        if field_id and field_id != str(uuid.uuid4()):
            return f"#{field_id}"
        if name:
            return f"{tag}[name='{name}']"
        return tag
