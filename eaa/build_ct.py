"""Deterministic source-preserving CT indicator -> strategy conversion.

This is a text transformation and static contract, NOT a Pine compiler.
The uploaded indicator is the only strategy source; public BACKTEST is unused.
"""
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'pine/eaa/reference/EAA_CT_SCALPER_INDICATOR_ORIGINAL_FROM_CHAT_2026-10-10.pine'
TARGET = ROOT / 'pine/eaa/EAA_CT_SCALPER_STRATEGY_V1.pine'
SOURCE_SHA = '9fa2463f2b27ae54554ea24290c38b9cd068ac240b61da7ca7b7cf44feed2b30'


def block(source, start, end):
    return source[source.index(start):source.index(end)]


def template(name):
    return (ROOT / 'eaa/ct_templates' / (name + '.pinefrag')).read_text()


def build():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA, 'Unexpected original source'
    src = raw.decode('utf-8')
    assert src.count('indicator(') == 1 and src.rstrip().endswith('message="CT EXIT SELL @ {{close}}")')
    prefix = src[:src.index('// ── OPEN TICKET FUNCTION')]
    prefix = prefix.replace('indicator("NQ/MNQ CT Scalper", overlay=true, max_lines_count=500, max_labels_count=500, max_boxes_count=500)', template('header').rstrip())
    # Preserve f_starStr; remove only the visual ticket type and array.
    a = prefix.index('// ── TRADE TICKET SYSTEM')
    b = prefix.index('f_starStr', a)
    prefix = prefix[:a] + prefix[b:]
    candidates = block(src, '// ── ENTRY GATES', '// ── TICKET PROCESSING')
    # Twelve original action bodies become raw candidates. All conditions,
    # feature computations, TP/SL formulas and priority gates remain identical.
    pattern = re.compile(r'            ctEntryPrice := close\n.*?            ct(Long|Short)FiredThisBar := true', re.S)
    matches = list(pattern.finditer(candidates))
    assert len(matches) == 12
    def candidate(match):
        body = match.group(0)
        side = match.group(1)
        kind = re.search(r'f_openTicket\([^\n]+, "(FADE|DIV|TRAP|AGG|ABSORB|VRZ)"\)', body).group(1)
        return (f'            eaaRaw{side}Sl := slCand\n'
                f'            eaaRaw{side}Tp := tpCand\n'
                f'            eaaRaw{side}Kind := "{kind}"\n'
                f'            ct{side}FiredThisBar := true')
    candidates = pattern.sub(candidate, candidates)
    smart = block(src, '// ── SMART EXIT', '// ── EXECUTE EXITS')
    visuals = block(src, '// ── ENTRY / EXIT PLOTSHAPES', '// ── ALERTS')
    # A divergence is known at confirmation, not at the pivot five bars ago.
    assert visuals.count('offset=-divLookback') == 4
    visuals = visuals.replace('offset=-divLookback', 'offset=0')
    return prefix + template('state') + candidates + smart + template('dispatch') + visuals + template('diagnostics')


if __name__ == '__main__':
    code = build()
    TARGET.write_text(code, encoding='utf-8')
    print(f'{TARGET.name}: {len(code.splitlines())} lines, SHA256 {hashlib.sha256(code.encode()).hexdigest()}')
