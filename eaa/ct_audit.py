"""Reproducible text-level evidence. This does not parse or compile Pine."""
import hashlib
import re
from .build_ct import SOURCE, TARGET, SOURCE_SHA, build, block


def executable_text(text):
    """Blank comments and strings, preserving line boundaries for simple checks."""
    out, i, quote = [], 0, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == '\\':
                out.extend('  ')
                i += 2
                continue
            if c == quote:
                quote = None
            out.append('\n' if c == '\n' else ' ')
        elif text[i:i+2] == '//':
            end = text.find('\n', i)
            end = len(text) if end == -1 else end
            out.extend(' ' * (end-i))
            i = end
            continue
        elif c in ('"', "'"):
            quote = c
            out.append(' ')
        else:
            out.append(c)
        i += 1
    if quote:
        raise ValueError('Unclosed string')
    return ''.join(out)


def balanced(text):
    stack = []
    closing = {')': '(', ']': '[', '}': '{'}
    for c in executable_text(text):
        if c in '([{':
            stack.append(c)
        elif c in closing and (not stack or stack.pop() != closing[c]):
            return False
    return not stack


def normalize_actions(section, original):
    # Independent, line-oriented normalization of only the twelve action bodies.
    start = '            ctEntryPrice := close' if original else '            eaaRaw'
    result, skipping = [], False
    for line in section.splitlines(keepends=True):
        if not skipping and line.startswith(start):
            skipping = True
        if skipping:
            if re.fullmatch(r'            ct(?:Long|Short)FiredThisBar := true\n?', line):
                result.append(line)
                skipping = False
        else:
            result.append(line)
    if skipping:
        raise ValueError('Incomplete candidate action')
    return ''.join(result)


def audit():
    original, converted = SOURCE.read_text(), TARGET.read_text()
    raw, out = SOURCE.read_bytes(), TARGET.read_bytes()
    src_prefix = block(original, '// ── INPUTS', '// ── OPEN TICKET FUNCTION')
    src_prefix = src_prefix[:src_prefix.index('// ── TRADE TICKET SYSTEM')] + src_prefix[src_prefix.index('f_starStr'):]
    dst_prefix = block(converted, '// ── INPUTS', '// ── EAA ACTUAL BROKER STATE')
    src_gates = block(original, '// ── ENTRY GATES', '// ── TICKET PROCESSING')
    dst_gates = block(converted, '// ── ENTRY GATES', '// ── SMART EXIT')
    src_visual = block(original, '// ── ENTRY / EXIT PLOTSHAPES', '// ── ALERTS')
    dst_visual = block(converted, '// ── ENTRY / EXIT PLOTSHAPES', '// ── EAA DIAGNOSTICS')
    code = executable_text(converted)
    models = ('FADE', 'DIV', 'TRAP', 'AGG', 'ABSORB', 'VRZ')
    checks = {
        'uploaded_original_sha256': hashlib.sha256(raw).hexdigest() == SOURCE_SHA,
        'uploaded_original_size_lines': len(raw) == 110723 and len(original.splitlines()) == 1871,
        'complete_source_sentinels': '//@version=6' in original and original.count('alertcondition(') == 6 and original.rstrip().endswith('message="CT EXIT SELL @ {{close}}")'),
        'deterministic_build': converted == build(),
        'all_original_inputs_exact': all(line in converted.splitlines() for line in original.splitlines() if re.search(r'\binput\.', line)),
        'entire_feature_pipeline_unchanged': src_prefix == dst_prefix,
        'entire_candidate_logic_unchanged': normalize_actions(src_gates, True) == normalize_actions(dst_gates, False),
        'all_six_models_both_directions_same_priority': all(re.findall(r'eaaRaw' + side + r'Kind := "([A-Z]+)"', dst_gates) == list(models) for side in ('Long', 'Short')),
        'smart_exit_logic_exact': block(original, '// ── SMART EXIT', '// ── EXECUTE EXITS') == block(converted, '// ── SMART EXIT', '// ── EAA REAL ORDER DISPATCH'),
        'smart_exit_still_disabled': converted.count('math.max(16.0, math.min(16.0,') == 2,
        'single_original_footprint_call': code.count('request.footprint(') == 1 and 'request.footprint(50, 70)' in converted,
        'visuals_only_confirmation_offset_changed': src_visual.replace('offset=-divLookback', 'offset=0') == dst_visual,
        'no_virtual_ticket_or_indicator_alerts': not re.search(r'\b(?:TixEntry|activeTix|f_openTicket|indicator|alert|alertcondition)\s*\(', code) and 'activeTix' not in code,
        'one_actual_entry_dispatch': code.count('strategy.entry(') == 1,
        'single_slot_and_no_reversal': 'pyramiding=0' in code and 'strategy.position_size == 0 and eaaSide == 0 and not eaaClosedNow and not eaaUnfilledNow' in code,
        'entry_bracket_same_calculation': code.index('strategy.exit(', code.index('strategy.entry(')) > code.index('strategy.entry('),
        'next_tick_bar_close_calculation': all(s in code for s in ('calc_on_every_tick=false', 'calc_on_order_fills=false', 'process_orders_on_close=false', 'if barstate.isconfirmed')),
        'cancel_and_immediate_session_flat': 'strategy.cancel_all()' in code and 'immediately=true' in code and 'f_eaaSessionOpen(time_close, 1004)' in code,
        'data_guard_enabled': 'input.bool(true, "Require 11 consecutive footprint bars"' in converted and 'eaaFootprintStreak >= 11' in code,
        'rejects_partial_positions': 'math.abs(strategy.position_size) != eaaContracts' in code and 'math.abs(strategy.closedtrades.size(tradeNo)) != eaaContracts' in code and 'or not expectedExit' in code,
        'unfilled_not_exposure': 'eaaExitOnCurrentBar and (strategy.position_size != 0 or eaaClosedNow)' in code,
        'delayed_session_exit_not_next_bar_exposure': 'strategy.closedtrades.exit_bar_index(strategy.closedtrades - 1) == bar_index' in code,
        'stress_cannot_improve_same_trade_native_net': 'math.min(eaaClosedNativeNet, adverseNet)' in code,
        'no_negative_history_index': not re.search(r'\[\s*-\s*\d+', code),
        'balanced_delimiters_not_compilation': balanced(converted),
    }
    return {
        'checks': checks,
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'strategy_sha256': hashlib.sha256(out).hexdigest(),
        'source_bytes': len(raw), 'strategy_bytes': len(out),
        'source_lines': len(original.splitlines()), 'strategy_lines': len(converted.splitlines()),
        'original_input_count': len(re.findall(r'\binput\.', executable_text(original))),
        'plot_calls': len(re.findall(r'\bplot(?:shape)?\(', code)),
        'request_calls': len(re.findall(r'\brequest\.', code)),
        'pine_compiled': False, 'tradingview_run': False,
        'signal_parity_on_market_data_verified': False,
    }
