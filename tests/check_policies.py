"""Static checks for the API Management policy files.

- every file is well-formed XML once placeholders are substituted
- every placeholder used in a policy is substituted by the Bicep module that loads it
- named values referenced as {{name}} are created in apim.bicep
- policies never read the response body (it breaks MCP streaming)
"""

from __future__ import annotations

import re
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICIES = ROOT / "infra" / "policies"
MODULES = ROOT / "infra" / "modules"


def strip_expressions(text: str) -> str:
    """Replace policy expressions @(...) and @{...} with a token, as API Management
    does before it parses the XML, so the remaining document can be checked."""
    out, i = [], 0
    pairs = {"(": ")", "{": "}"}
    while i < len(text):
        if text[i] == "@" and i + 1 < len(text) and text[i + 1] in pairs:
            open_, close, depth, j = text[i + 1], pairs[text[i + 1]], 0, i + 1
            in_str = False
            while j < len(text):
                c = text[j]
                if c == '"' and text[j - 1] != "\\":
                    in_str = not in_str
                elif not in_str and c == open_:
                    depth += 1
                elif not in_str and c == close:
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:
                raise ValueError(f"unbalanced expression at offset {i}")
            out.append("EXPR")
            i = j + 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def main() -> int:
    errors = []
    bicep = "\n".join(p.read_text() for p in MODULES.glob("*.bicep"))
    named_values = set(re.findall(r"namedValues@[^']+' = \{\s*parent: apim\s*name: '([^']+)'", bicep))
    for policy in sorted(POLICIES.glob("*.xml")):
        text = policy.read_text()
        placeholders = set(re.findall(r"__([A-Z_]+)__", text))
        for ph in placeholders:
            if not re.search(rf"'__{ph}__'", bicep):
                errors.append(f"{policy.name}: placeholder __{ph}__ is never replaced in Bicep")
        for nv in set(re.findall(r"\{\{([a-z0-9-]+)\}\}", text)):
            if nv not in named_values:
                errors.append(f"{policy.name}: named value {{{{{nv}}}}} is not created in apim.bicep")
        code = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        if "Response.Body" in code:
            errors.append(f"{policy.name}: reads context.Response.Body")
        if "&&" in code:
            errors.append(f"{policy.name}: '&&' is not valid in XML; nest <choose> blocks instead")
        sample = strip_expressions(re.sub(r"__([A-Z_]+)__", "x", code))
        try:
            xml.dom.minidom.parseString(sample)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{policy.name}: not well-formed XML: {exc}")
        print(f"checked {policy.name}")
    for e in errors:
        print(f"ERROR {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
