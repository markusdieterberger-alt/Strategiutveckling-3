#!/usr/bin/env python3
"""Deterministically derive isolated research copies; never edit the source.

This is a source transformer, not a Pine compiler or CT/footprint emulator.
"""
from pathlib import Path
import argparse, hashlib, difflib, json, re

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = 'c386f4f7d3e30e3ebfe57ebe5e35e40c5560fda88b7f38296405d080ebbcf8e8'

def replace(s, old, new, count=1):
    if s.count(old) != count:
        raise ValueError(f'Patch anchor expected {count}, found {s.count(old)}: {old[:100]}')
    return s.replace(old, new)

def derive(source, diagnostic=False):
    version = 'EAA_CT_DIAG_2.0.0' if diagnostic else 'EAA_CT_V2_2.0.0'
    title = 'EAA CT Diagnostic V1-V2 - ISOLATED QA' if diagnostic else 'EAA CT Scalper V2 - Non-Repaint & Alert Parity DEV'
    s = source[source.index('strategy('):]
    header = ('//@version=6\n'
              '// Isolated research implementation. COMPILE NOT VERIFIED at source release.\n'
              '// Native compile/execution evidence is versioned separately in QA_STATUS.json.\n'
              '// Non-Repaint is a design objective, NOT a verified property of footprint/feed data.\n'
              '// No broker integration; native TV emulator is the only trade book.\n'
              f'// Derived from immutable V1 SHA256 {SOURCE_SHA}\n'
              '// Preserve the active V1 and all its alerts. Default test dates remain V1 dates.\n')
    s = replace(s, 'strategy("EAA CT Scalper STRATEGY V1"', f'strategy("{title}"')
    s = replace(s, 'int eaaStressSlip = input.int(1, "Stress stop slippage (ticks)", minval=0, group=eaaGroup,\n     tooltip="Only the separate stress ledger. Match Properties slippage. Does NOT change actual strategy orders.")\n', '')
    setup = (ROOT/'templates/setup.pine.txt').read_text().replace('__VERSION__',version)
    if diagnostic:
        setup += '\nbool v2ConfirmedHtf = input.bool(false, "ONLY intervention: confirmed HTF", group=v2Group)\n'
    else:
        setup += '\nbool v2ConfirmedHtf = true\n'
        setup += ('// Fail visibly on unsupported repeated/intrabar calculations; do not silently\n'
                  '// mutate cumulative/stateful V1 logic under Properties overrides.\n'
                  'if not barstate.isconfirmed or v2CalcInBar > 1\n'
                  '    runtime.error("V2 requires one calculation per closed bar. Disable On every tick and After order is filled; capture Properties.")\n')
    s = replace(s, '// New protocol constraints, not changes to the original signal filters.', setup+'\n// New protocol constraints, not changes to the original signal filters.')
    s = s.replace('EAA CT V1 protocol', 'EAA CT V2 protocol').replace('EAA CT V1 requires', 'EAA CT V2 requires')
    # Offset every requested field INSIDE HTF context, never the merged 1m result.
    a=s.index('// ── HTF GATE'); b=s.index('// HTF confluence score',a)
    htf=[]
    for tf,prefix,n in [('5','h5',4),('15','h15',4),('60','h60',4),('240','h4',2)]:
        names=[prefix+'f',prefix+'s']+([prefix+'c',prefix+'mid'] if n==4 else [])
        expr=['ta.ema(close, 9)','ta.ema(close, 21)']+(['close','(ta.highest(high, 20) + ta.lowest(low, 20)) / 2'] if n==4 else [])
        offset=['ta.ema(close, 9)[1]','ta.ema(close, 21)[1]']+(['close[1]','(ta.highest(high, 20)[1] + ta.lowest(low, 20)[1]) / 2'] if n==4 else [])
        if diagnostic:
            htf.append('['+', '.join(x+'Legacy' for x in names)+f', {prefix}LegacyClose] = request.security(syminfo.tickerid, "{tf}",\n    ['+', '.join(expr+['time_close'])+'], lookahead=barmerge.lookahead_off)')
            htf.append('['+', '.join(x+'Confirmed' for x in names)+f', {prefix}ConfirmedClose] = request.security(syminfo.tickerid, "{tf}",\n    ['+', '.join(offset+['time_close[1]'])+'], lookahead=barmerge.lookahead_on)')
            for name in names:
                htf.append(f'float {name} = v2ConfirmedHtf ? {name}Confirmed : {name}Legacy')
            htf.append(f'int {prefix}KnownClose = v2ConfirmedHtf ? {prefix}ConfirmedClose : {prefix}LegacyClose')
        else:
            htf.append('['+', '.join(names)+f', {prefix}KnownClose] = request.security(syminfo.tickerid, "{tf}",\n    ['+', '.join(offset+['time_close[1]'])+'], lookahead=barmerge.lookahead_on)')
    htf += ['bool v2HtfReady = not na(h5KnownClose) and not na(h15KnownClose) and not na(h60KnownClose) and not na(h4KnownClose)',
            'if v2ConfirmedHtf and v2HtfReady and math.max(math.max(h5KnownClose, h15KnownClose), math.max(h60KnownClose, h4KnownClose)) > time',
            '    runtime.error("Confirmed HTF known-time invariant failed.")','']
    s=s[:a]+'// Confirmed HTF timestamps are observational; no new warmup filter.\n'+'\n'.join(htf)+'\n'+s[b:]
    s=replace(s,'float fpVAH = na','bool v2PocFresh = false\nfloat fpVAH = na')
    s=replace(s,'    if not na(pocRow)\n        fpPocMid :=','    if not na(pocRow)\n        v2PocFresh := true\n        fpPocMid :=')
    # Remove V1's counterfactual PnL ledger, which never controlled orders.
    remove_lines=['var float eaaStressStop = na','var float eaaStressNet = 0.0','float eaaClosedStressNet = na',
                  '    float adverseNet = eaaTradeAmbiguous ? eaaSide * (eaaStressStop - actualEntry) * syminfo.pointvalue * qty - fees : eaaClosedNativeNet',
                  '    eaaClosedStressNet := math.min(eaaClosedNativeNet, adverseNet)',
                  '    eaaStressNet += eaaClosedStressNet']
    for line in remove_lines:s=replace(s,line+'\n','')
    s=re.sub(r'^\s*eaaStressStop := na\n','',s,flags=re.M)
    a=s.index('    // Stop-first OHLC envelope:');b=s.index('\nif not eaaSawFill',a)
    s=s[:a]+s[b:]
    s=replace(s,'var string eaaEntryId = ""', 'var string eaaEntryId = ""\n'+(ROOT/'templates/state.pine.txt').read_text())
    s=replace(s,'if not eaaSawFill and (strategy.position_size != 0 or eaaClosedNow)',
      'bool v2ObserveEntry = not eaaSawFill and (strategy.position_size != 0 or eaaClosedNow)\n'
      'float v2EntryPriceObserved = na\nint v2EntryTimeObserved = na\nfloat v2ExitPriceObserved = na\nint v2ExitReason = 0\nfloat v2ActualQty = na\n'
      'if v2ObserveEntry\n'
      '    v2EntryPriceObserved := strategy.position_size != 0 ? strategy.position_avg_price : strategy.closedtrades.entry_price(strategy.closedtrades - 1)\n'
      '    v2EntryTimeObserved := strategy.position_size != 0 ? strategy.opentrades.entry_time(0) : strategy.closedtrades.entry_time(strategy.closedtrades - 1)\n'
      '    v2ActualQty := strategy.position_size != 0 ? math.abs(strategy.position_size) : math.abs(strategy.closedtrades.size(strategy.closedtrades - 1))\n'
      '    if v2PineLogs\n'
      '        log.info("NATIVE_ENTRY_OBSERVED | " + v2EntryPayload + " | observed_at_ms=" + str.tostring(time_close) + " | native_entry_ms=" + str.tostring(v2EntryTimeObserved) + " | native_price=" + str.tostring(v2EntryPriceObserved, format.mintick))\n'
      'if v2ObserveEntry')
    s=replace(s, '    string exitComment = strategy.closedtrades.exit_comment(tradeNo)',
      '    string exitComment = strategy.closedtrades.exit_comment(tradeNo)\n'
      '    v2ExitReason := exitComment == "SL" ? 1 : exitComment == "TP" ? 2 : exitComment == "PAT" ? 3 : exitComment == "SESSION_OR_TEST_END" ? 4 : 9\n'
      '    v2ExitPriceObserved := strategy.closedtrades.exit_price(tradeNo)\n'
      '    v2ActualQty := math.abs(strategy.closedtrades.size(tradeNo))\n'
      '    if v2PineLogs\n'
      '        log.info("NATIVE_EXIT_OBSERVED | " + v2EntryPayload + " | observed_at_ms=" + str.tostring(time_close) + " | native_exit_ms=" + str.tostring(strategy.closedtrades.exit_time(tradeNo)) + " | native_price=" + str.tostring(v2ExitPriceObserved, format.mintick) + " | reason=" + exitComment)')
    # Observation masks follow actual original priority, not hypothetical lower-priority trades.
    s=replace(s,'// Raw candidates, evaluated even while occupied. Their filters are unchanged.',
      '// Raw candidates, evaluated even while occupied. Their filters are unchanged.\n'
      'int v2EvalMask = 0\nint v2FlowMask = 0\nint v2RawMask = 0\nint v2PrioritySkipped = 0')
    for model,var,bit in [('FADE','Fade',1),('DIV','Div',2),('TRAP','Trap',4),('AGG','Agg',8),('ABSORB','Absorb',16),('VRZ','Vrz',32)]:
        for side,mul in [('Long',1),('Short',64)]:
            anchor='if use'+var+' and ctGate'+side+' and not ct'+side+'FiredThisBar'
            start=s.index(anchor); end=s.find('\n\n',start)
            block=s[start:end]; lines=block.splitlines()
            lines.insert(1,f'    v2EvalMask += {bit*mul}')
            # First inner conditional is the model's flow/score criterion.
            k=next(i for i,l in enumerate(lines) if l.startswith('    if '))
            lines.insert(k+1,f'        v2FlowMask += {bit*mul}')
            anchor2=f'            eaaRaw{side}Kind := "{model}"'
            k=lines.index(anchor2);lines.insert(k+1,f'            v2RawMask += {bit*mul}')
            prefix=f'if use{var} and ct{side}FiredThisBar\n    v2PrioritySkipped += {bit*mul}\n'
            s=s[:start]+prefix+'\n'.join(lines)+s[end:]
    # Build gate snapshots before dispatch; levels calculated once by original code.
    s=replace(s,'int eaaSubmittedModel = 0', 'int eaaSubmittedModel = 0\n'+(ROOT/'templates/gates.pine.txt').read_text())
    s=replace(s,'                 alert_message="EAA_CT_V1|EXIT|SESSION_OR_TEST_END")',
      '                 alert_message=f_v2Intent("SESSION_OR_TEST_END", v2TradeContext, time_close))')
    s=replace(s,'alert_message="EAA_CT_V1|EXIT|PAT"','alert_message=f_v2Intent("PAT", v2TradeContext, time_close)')
    s=replace(s,'strategy.exit("CT_BRACKET",','strategy.exit(v2BracketId,',2)
    s=replace(s,'comment_profit="TP", comment_loss="SL", alert_message="EAA_CT_V1|EXIT|BRACKET")',
      'comment_profit="TP", comment_loss="SL", alert_message=v2BracketPayload, alert_profit=v2TpPayload, alert_loss=v2SlPayload)',2)
    s=replace(s,'            if validLevels\n','            v2LevelsValid := validLevels\n            v2CandidateSl := finalSl\n            v2CandidateTp := finalTp\n            if validLevels\n')
    s=replace(s,'                eaaEntryId := (isLongOrder ? "CT_L_" : "CT_S_") + kind',
      '                eaaEntryId := (isLongOrder ? "CT2_L_" : "CT2_S_") + kind + "_" + str.tostring(time_close)\n'
      '                v2BracketId := "CT2_X_" + str.tostring(time_close)')
    s=replace(s,'                eaaOrderSubmitted := true',
      '                v2SignalBarMs := time\n                v2SubmitMs := time_close\n'
      '                v2TradeContext := f_v2Context(kind, eaaSide, eaaEntryId, v2BracketId, finalSl, finalTp, v2ExecGates, v2RawMask, v2HtfSnapshot, v2FpSnapshot)\n'
      '                v2EntryPayload := f_v2Intent("ENTRY", v2TradeContext, time_close)\n'
      '                v2BracketPayload := f_v2Intent("BRACKET", v2TradeContext, time_close)\n'
      '                v2TpPayload := f_v2Intent("TP", v2TradeContext, time_close)\n'
      '                v2SlPayload := f_v2Intent("SL", v2TradeContext, time_close)\n'
      '                eaaOrderSubmitted := true')
    s=replace(s,'alert_message="EAA_CT_V1|ENTRY|" + eaaEntryId','alert_message=v2EntryPayload')
    # Replace misleading micro-pattern shapes, not their calculations, with explicit QA fields.
    a=s.index('// ── ENTRY / EXIT PLOTSHAPES'); b=s.index('// ── DASHBOARD',a)
    s=s[:a]+'// Internal-pattern shapes removed: they were not orders or fills.\n'+s[b:]
    a=s.index('// ── EAA DIAGNOSTICS / EXPORT FIELDS')
    s=s[:a]+(ROOT/'templates/telemetry.pine.txt').read_text()
    return header+s

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'reference/EAA_CT_SCALPER_STRATEGY_V1.pine');args=parser.parse_args()
    b=args.source.read_bytes();assert hashlib.sha256(b).hexdigest()==SOURCE_SHA,'SOURCE HASH MISMATCH'
    src=b.decode('utf-8');(ROOT/'pine').mkdir(exist_ok=True);(ROOT/'diff').mkdir(exist_ok=True)
    for diagnostic,name in [(False,'EAA_CT_SCALPER_V2_DEV.pine'),(True,'EAA_CT_DIAGNOSTIC_V1_V2.pine')]:
        out=derive(src,diagnostic);(ROOT/'pine'/name).write_text(out)
        diff=''.join(difflib.unified_diff(src.splitlines(True),out.splitlines(True),fromfile='PRISTINE_V1',tofile=name))
        (ROOT/'diff'/(name+'.diff')).write_text(diff)
        print(name,len(out.encode()),hashlib.sha256(out.encode()).hexdigest())

if __name__=='__main__':main()
