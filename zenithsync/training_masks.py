"""Instrument the supplied Gemma template without changing rendered content.

Only this audited template layout is supported. Generation annotations label
assistant reasoning/calls/content and terminal markers, never tool results.
"""

import hashlib

from .conversation import normalize_history


def annotate_template(template: str, expected_sha256: str) -> str:
    if hashlib.sha256(template.encode('utf-8')).hexdigest() != expected_sha256:
        raise ValueError('Unqualified chat template')
    if '{% generation' in template or '{%- generation' in template:
        raise ValueError('Template already has generation annotations')
    start = '    {#- Render reasoning/reasoning_content as thinking channel -#}'
    end = "            {%- set ns_tr_out = namespace(flag=false) -%}"
    content = '            {{- captured_content -}}'
    terminal = "            {{- '<turn|>\\n' -}}"
    for anchor in [start, end, content, terminal]:
        if template.count(anchor) != 1:
            raise ValueError('Unsupported template structure')
    # The first region contains only assistant-generated reasoning/tool calls
    # for normalized histories. Tool results start after ns_tr_out.
    template = template.replace(start, '{% generation %}' + start, 1)
    template = template.replace(end, '{% endgeneration %}' + end, 1)
    template = template.replace(content,
        "{% if role == 'model' %}{% generation %}" + content +
        "{% endgeneration %}{% else %}" + content + '{% endif %}', 1)
    return template.replace(terminal,
        "{% if role == 'model' %}{% generation %}" + terminal +
        "{% endgeneration %}{% else %}" + terminal + '{% endif %}', 1)


def normalize_training_history(messages, *, allowed_tools, terminal_call_tools=None):
    """Keep complete exchanges by default; permit one named terminal call explicitly."""
    if terminal_call_tools is not None:
        if (not isinstance(terminal_call_tools, set) or not terminal_call_tools
                or not isinstance(allowed_tools, set) or not terminal_call_tools <= allowed_tools):
            raise ValueError('Terminal tools must be an explicit nonempty subset of allowed tools')
    normalized = normalize_history(messages, allowed_tools=allowed_tools,
                                   allow_pending=terminal_call_tools is not None)
    if terminal_call_tools is not None:
        final = normalized[-1]
        calls = final.get('tool_calls', [])
        if (final['role'] != 'assistant' or len(calls) != 1
                or calls[0]['function']['name'] not in terminal_call_tools):
            raise ValueError('Explicit terminal mode requires one final allowed terminal call')
    return normalized


def assistant_training_tokens(tokenizer, messages, *, template_sha256, allowed_tools,
                              tools=None, terminal_call_tools=None):
    """Require exact native rendering and token IDs before returning labels.

    No truncation, packing, padding, or inference about missing messages occurs.
"""
    messages = normalize_training_history(messages, allowed_tools=allowed_tools,
                                          terminal_call_tools=terminal_call_tools)
    template = tokenizer.chat_template
    annotated = annotate_template(template, template_sha256)
    options = {'add_generation_prompt': False, 'tools': tools}
    native_text = tokenizer.apply_chat_template(messages, tokenize=False, **options)
    annotated_text = tokenizer.apply_chat_template(messages, chat_template=annotated,
                                                    tokenize=False, **options)
    if native_text != annotated_text:
        raise ValueError('Generation annotations changed native serialization')
    native_ids = tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False, **options)
    encoded = tokenizer.apply_chat_template(messages, chat_template=annotated, tokenize=True,
        return_dict=True, return_assistant_tokens_mask=True, **options)
    if encoded['input_ids'] != native_ids:
        raise ValueError('Annotated tokenization differs from native tokenization')
    mask = encoded['assistant_masks']
    if len(mask) != len(native_ids) or any(type(x) is not int or x not in [0, 1] for x in mask):
        raise ValueError('Invalid assistant-token mask')
    from transformers.utils.chat_template_utils import render_jinja_template
    texts, spans = render_jinja_template(conversations=[messages], chat_template=annotated,
        tools=tools, return_assistant_tokens_mask=True, add_generation_prompt=False,
        **tokenizer.special_tokens_map)
    if texts != [native_text]:
        raise ValueError('Assistant-span renderer differs from tokenizer rendering')
    offsets = tokenizer(native_text, add_special_tokens=False, return_offsets_mapping=True)
    if offsets['input_ids'] != native_ids:
        raise ValueError('Offset tokenization differs from native tokenization')
    for active, (start, end) in zip(mask, offsets['offset_mapping'], strict=True):
        overlap = any(start < right and end > left for left, right in spans[0])
        contained = start < end and any(left <= start and end <= right for left, right in spans[0])
        if overlap != contained or bool(active) != contained:
            raise ValueError('Token crosses a supervision boundary or has an inconsistent mask')
    labels = [token if active else -100 for token, active in zip(native_ids, mask, strict=True)]
    if not any(x != -100 for x in labels[1:]):
        raise ValueError('No supervised next-token target')
    return {'input_ids': native_ids, 'labels': labels, 'assistant_mask': mask}
