def format_policy_sources(sources):
    if not sources:
        return "No policy sources retrieved."

    lines = []
    for i, source in enumerate(sources, start=1):
        lines.append(
            f"[Source {i}] "
            f"source_id={source.get('source_id', 'unknown')}; "
            f"document_id={source.get('document_id', 'unknown')}; "
            f"version={source.get('version_label') or 'active'}; "
            f"authority={source.get('authority_level', 'unknown')}; "
            f"text={source.get('text', '')}"
        )
    return "\n".join(lines)

def format_tool_result(result):
    if not result:
        return "No database tool result."
    return str(result)
