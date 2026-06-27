import os

def patch_demo_html(file_path):
    print(f"Patching {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Patch the Speaker Mode Ternary/Mitigation check (lines 2951-2975 in demo.html / 2893-2928 in backend/demo.html)
    # We want to replace the hardcoded "speakerScore >= 70" check with "speakerScore >= speakerDynamicThreshold" and insert the Adaptive Threshold Tuning widget.
    target_speaker_mitigation = """                                         {/* Threat alert mitigations */}
                                         {speakerScore >= 70 ? (
                                             <div class="p-3 bg-shieldRed/10 border border-shieldRed/30 rounded-xl flex flex-col gap-2.5 animate-pulse">
                                                 <div class="flex items-center gap-2">
                                                     <span class="text-lg">🚨</span>
                                                     <span class="text-xs font-black text-shieldRed uppercase tracking-wider">CRITICAL THREAT FLAG</span>
                                                 </div>
                                                 <p class="text-[10px] text-slate-400 leading-relaxed font-semibold">
                                                     <strong>Recommendation:</strong> Hang up immediately. Caller matches impersonation threat patterns.
                                                 </p>
                                                 <div class="flex gap-2 justify-end mt-1">
                                                     <button onClick={stopSpeakerListening} class="px-3 py-1.5 bg-shieldRed hover:bg-shieldRed/80 text-white text-[10px] font-extrabold rounded-lg border-none transition-all cursor-pointer">
                                                         Hang Up Call
                                                     </button>
                                                     <button onClick={handleSaveSpeakerIncident} class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold rounded-lg border-none transition-all cursor-pointer">
                                                         Log Incident
                                                     </button>
                                                 </div>
                                             </div>
                                         ) : (
                                             <div class="p-3 bg-slate-900/60 border border-darkBorder/40 rounded-xl flex items-center gap-2">
                                                 <span class="text-base text-shieldGreen">🛡️</span>
                                                 <span class="text-[10px] text-slate-400 font-medium font-semibold">Acoustic Shield status normal. Listening for risk triggers...</span>
                                             </div>
                                         )}"""

    replacement_speaker_mitigation = """                                         {/* Adaptive Threshold Tuning Engine Details (Speaker Mode) */}
                                         {dynamicThresholdEnabled && (
                                             <div class="flex flex-col gap-1.5 bg-slate-950/50 p-2.5 rounded-xl border border-slate-900/80 mb-3">
                                                 <div class="flex justify-between items-center text-[9px] font-bold text-slate-400">
                                                     <span>⚡ ADAPTIVE THRESHOLD TUNING ENGINE</span>
                                                     <span class="font-mono text-slate-300">Active: {speakerDynamicThreshold}% (Base: {detectionSensitivity}%)</span>
                                                 </div>
                                                 <div class="flex flex-wrap gap-2 text-[8px] font-mono leading-none">
                                                     <span class="text-slate-400">-5% (Unknown Caller)</span>
                                                     {speakerBadges.otpRequest && <span class="text-shieldRed font-bold">-20% (OTP Verification Block)</span>}
                                                     {speakerBadges.moneyTransfer && <span class="text-shieldRed font-bold">-15% (Financial Transfer)</span>}
                                                     {speakerBadges.urgencyDetected && <span class="text-shieldOrange">-10% (Urgency Language)</span>}
                                                     {speakerBadges.possibleSyntheticSpeech && <span class="text-shieldRed font-bold animate-pulse">-25% (Synthetic Voice Cloned)</span>}
                                                     {!speakerBadges.otpRequest && !speakerBadges.moneyTransfer && !speakerBadges.urgencyDetected && !speakerBadges.possibleSyntheticSpeech && <span class="text-slate-600">Waiting for risk triggers...</span>}
                                                 </div>
                                             </div>
                                         )}

                                         {/* Threat alert mitigations */}
                                         {speakerScore >= speakerDynamicThreshold ? (
                                             <div class="p-3 bg-shieldRed/10 border border-shieldRed/30 rounded-xl flex flex-col gap-2.5 animate-pulse">
                                                 <div class="flex items-center gap-2">
                                                     <span class="text-lg">🚨</span>
                                                     <span class="text-xs font-black text-shieldRed uppercase tracking-wider">CRITICAL THREAT FLAG</span>
                                                 </div>
                                                 <p class="text-[10px] text-slate-400 leading-relaxed font-semibold">
                                                     <strong>Recommendation:</strong> Hang up immediately. Caller matches impersonation threat patterns.
                                                 </p>
                                                 <div class="flex gap-2 justify-end mt-1">
                                                     <button onClick={stopSpeakerListening} class="px-3 py-1.5 bg-shieldRed hover:bg-shieldRed/80 text-white text-[10px] font-extrabold rounded-lg border-none transition-all cursor-pointer">
                                                         Hang Up Call
                                                     </button>
                                                     <button onClick={handleSaveSpeakerIncident} class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold rounded-lg border-none transition-all cursor-pointer">
                                                         Log Incident
                                                     </button>
                                                 </div>
                                             </div>
                                         ) : (
                                             <div class="p-3 bg-slate-900/60 border border-darkBorder/40 rounded-xl flex items-center gap-2">
                                                 <span class="text-base text-shieldGreen">🛡️</span>
                                                 <span class="text-[10px] text-slate-400 font-medium font-semibold">Acoustic Shield status normal. Listening for risk triggers...</span>
                                             </div>
                                         )}"""

    # Normalize line endings to find target block reliably
    content_norm = content.replace("\r\n", "\n")
    target_norm = target_speaker_mitigation.replace("\r\n", "\n")
    replacement_norm = replacement_speaker_mitigation.replace("\r\n", "\n")

    if target_norm in content_norm:
        content_norm = content_norm.replace(target_norm, replacement_norm)
        print("-> Successfully patched Speaker Mode mitigations & widget!")
    else:
        # Try finding a slightly simpler match if indentation is slightly different
        print("-> Speaker Mode mitigation block not found with standard indentation. Trying sub-string search...")
        # Fallback to replace the 70 threshold check on that block at least
        target_check = "{speakerScore >= 70 ? ("
        replacement_check = "{speakerScore >= speakerDynamicThreshold ? ("
        if target_check in content_norm:
            content_norm = content_norm.replace(target_check, replacement_check)
            print("-> Successfully patched Speaker score comparison check!")
        else:
            print("-> [WARNING] Speaker score comparison check target not found!")

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content_norm)

def patch_backend_demo_html(file_path):
    print(f"Patching {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    content_norm = content.replace("\r\n", "\n")

    # 1. State hook injection
    target_states = """            // Adaptive Detection Engine & Timeline states
            const [detectionMode, setDetectionMode] = useState('balanced'); // 'conservative' | 'balanced' | 'aggressive' | 'elderly'"""

    replacement_states = """            // Adaptive Detection Engine & Timeline states
            const [detectionMode, setDetectionMode] = useState('balanced'); // 'conservative' | 'balanced' | 'aggressive' | 'elderly'
            const [detectionSensitivity, setDetectionSensitivity] = useState(70); // range: 50-90
            const [riskTimelineEvents, setRiskTimelineEvents] = useState([]); // array of { time: string, factor: string, weight: number, cumulative: number }
            const [dynamicThresholdEnabled, setDynamicThresholdEnabled] = useState(true);
            const [simDynamicThreshold, setSimDynamicThreshold] = useState(70);
            const [speakerDynamicThreshold, setSpeakerDynamicThreshold] = useState(70);

            const calculateThreshold = (base, indicators) => {
                if (!dynamicThresholdEnabled) return base;
                let val = base;
                if (indicators.includes("Unknown Number")) val -= 5;
                if (indicators.includes("Impersonation Attempt")) val -= 10;
                if (indicators.includes("Urgency Language")) val -= 10;
                if (indicators.includes("Verification Request")) val -= 20;
                if (indicators.includes("Money Request")) val -= 15;
                if (indicators.includes("Synthetic Voice Indicators")) val -= 25;
                return Math.max(30, Math.min(95, val));
            };

            const calculateSpeakerThreshold = (base, badges) => {
                if (!dynamicThresholdEnabled) return base;
                let val = base;
                if (badges.otpRequest) val -= 20;
                if (badges.moneyTransfer) val -= 15;
                if (badges.urgencyDetected) val -= 10;
                if (badges.possibleSyntheticSpeech) val -= 25;
                return Math.max(30, Math.min(95, val));
            };

            // Reactively update dynamic thresholds
            useEffect(() => {
                setSimDynamicThreshold(calculateThreshold(detectionSensitivity, simActiveIndicators));
            }, [simActiveIndicators, detectionSensitivity, dynamicThresholdEnabled]);

            useEffect(() => {
                setSpeakerDynamicThreshold(calculateSpeakerThreshold(detectionSensitivity, speakerBadges));
            }, [speakerBadges, detectionSensitivity, dynamicThresholdEnabled]);

            useEffect(() => {
                if (simScore >= simDynamicThreshold) setSimRisk('CRITICAL');
                else if (simScore >= 45) setSimRisk('HIGH');
                else if (simScore >= 20) setSimRisk('MEDIUM');
                else setSimRisk('LOW');
            }, [simScore, simDynamicThreshold]);

            useEffect(() => {
                if (speakerScore >= speakerDynamicThreshold) setSpeakerRiskLevel('FRAUD');
                else if (speakerScore >= 40) setSpeakerRiskLevel('WARNING');
                else setSpeakerRiskLevel('SAFE');
            }, [speakerScore, speakerDynamicThreshold]);"""

    if target_states in content_norm:
        content_norm = content_norm.replace(target_states, replacement_states)
        print("-> Injected states, helpers, and hooks successfully!")
    else:
        print("-> [WARNING] States block target not found!")

    # 2. XAI Timeline Header & Details Box in backend/demo.html
    target_timeline_header = """                                             <div class="text-right">
                                                 <div class="text-[9px] font-bold text-slate-500 uppercase font-mono">Status vs Threshold ({detectionSensitivity}%)</div>
                                                 <span class={`text-[9px] font-bold px-2 py-0.5 rounded mt-1 inline-block ${simScore >= detectionSensitivity ? 'bg-shieldRed/15 text-shieldRed border border-shieldRed/30' : 'bg-shieldGreen/15 text-shieldGreen border border-shieldGreen/30'}`}>
                                                     {simScore >= detectionSensitivity ? '🚨 THREAT EXCEEDED' : '✓ SECURE SCREENING'}
                                                 </span>
                                             </div>
                                         </div>"""

    replacement_timeline_header = """                                             <div class="text-right">
                                                 <div class="text-[9px] font-bold text-slate-500 uppercase font-mono">
                                                     {dynamicThresholdEnabled ? 'Adaptive Threshold' : 'Static Threshold'} ({simDynamicThreshold}%)
                                                 </div>
                                                 <span class={`text-[9px] font-bold px-2 py-0.5 rounded mt-1 inline-block ${simScore >= simDynamicThreshold ? 'bg-shieldRed/15 text-shieldRed border border-shieldRed/30' : 'bg-shieldGreen/15 text-shieldGreen border border-shieldGreen/30'}`}>
                                                     {simScore >= simDynamicThreshold ? '🚨 THREAT EXCEEDED' : '✓ SECURE SCREENING'}
                                                 </span>
                                             </div>
                                         </div>

                                         {/* Adaptive Threshold Tuning Engine Details */}
                                         {dynamicThresholdEnabled && (
                                             <div class="flex flex-col gap-1.5 bg-slate-950/50 p-2.5 rounded-xl border border-slate-900/80 mt-1">
                                                 <div class="flex justify-between items-center text-[9px] font-bold text-slate-400">
                                                     <span>⚡ ADAPTIVE THRESHOLD TUNING ENGINE</span>
                                                     <span class="font-mono text-slate-300">Active: {simDynamicThreshold}% (Base: {detectionSensitivity}%)</span>
                                                 </div>
                                                 <div class="flex flex-wrap gap-2 text-[8px] font-mono leading-none">
                                                     {simActiveIndicators.includes("Unknown Number") && <span class="text-slate-400">-5% (Unknown Number)</span>}
                                                     {simActiveIndicators.includes("Impersonation Attempt") && <span class="text-shieldOrange">-10% (Impersonation)</span>}
                                                     {simActiveIndicators.includes("Urgency Language") && <span class="text-shieldOrange">-10% (Urgency Language)</span>}
                                                     {simActiveIndicators.includes("Verification Request") && <span class="text-shieldRed font-bold">-20% (OTP Verification Block)</span>}
                                                     {simActiveIndicators.includes("Money Request") && <span class="text-shieldRed font-bold">-15% (Financial Transfer)</span>}
                                                     {simActiveIndicators.includes("Synthetic Voice Indicators") && <span class="text-shieldRed font-bold animate-pulse">-25% (Synthetic Voice Cloned)</span>}
                                                     {simActiveIndicators.length <= 1 && <span class="text-slate-600">Waiting for risk triggers...</span>}
                                                 </div>
                                             </div>
                                         )}"""

    if target_timeline_header in content_norm:
        content_norm = content_norm.replace(target_timeline_header, replacement_timeline_header)
        print("-> Updated XAI Timeline Header successfully!")
    else:
        print("-> [WARNING] XAI Timeline Header target not found!")

    # 3. Dynamic Threshold check in simulation loop
    target_sim_loop_1 = """                        const finalScoreVal = getScoreForStep(simKey, scenario.dialogue.length - 1);
                        if (simKey !== 'voice_clone' && finalScoreVal >= detectionSensitivity && simLineIndex === scenario.dialogue.length - 1) {"""

    replacement_sim_loop_1 = """                        const finalScoreVal = getScoreForStep(simKey, scenario.dialogue.length - 1);
                        const finalThreshold = calculateThreshold(detectionSensitivity, Array.from(new Set([...simActiveIndicators, "Unknown Number", ...newIndicators])));
                        if (simKey !== 'voice_clone' && finalScoreVal >= finalThreshold && simLineIndex === scenario.dialogue.length - 1) {"""

    target_sim_loop_2 = """                    const finalScoreVal = getScoreForStep(simKey, scenario.dialogue.length - 1);
                    if (finalScoreVal < detectionSensitivity) {"""

    replacement_sim_loop_2 = """                    const finalScoreVal = getScoreForStep(simKey, scenario.dialogue.length - 1);
                    const finalThreshold = calculateThreshold(detectionSensitivity, simActiveIndicators);
                    if (finalScoreVal < finalThreshold) {"""

    if target_sim_loop_1 in content_norm:
        content_norm = content_norm.replace(target_sim_loop_1, replacement_sim_loop_1)
        print("-> Updated Simulation loop threat checks (part 1) successfully!")
    else:
        print("-> [WARNING] Simulation loop threat checks (part 1) target not found!")

    if target_sim_loop_2 in content_norm:
        content_norm = content_norm.replace(target_sim_loop_2, replacement_sim_loop_2)
        print("-> Updated Simulation loop threat checks (part 2) successfully!")
    else:
        print("-> [WARNING] Simulation loop threat checks (part 2) target not found!")

    # 4. Settings slider toggles (Add to both settings blocks)
    # Block 1 slider end
    target_slider_1 = """                                                <div class="flex justify-between text-[8px] text-slate-500 font-mono tracking-wide mt-0.5">
                                                    <span class="flex flex-col gap-0.5">
                                                        <span class="font-bold">50 (Aggressive)</span>
                                                        <span>Flags early warnings</span>
                                                    </span>
                                                    <span class="flex flex-col gap-0.5 text-center">
                                                        <span class="font-bold">70 (Balanced)</span>
                                                        <span>Recommended</span>
                                                    </span>
                                                    <span class="flex flex-col gap-0.5 text-right">
                                                        <span class="font-bold">90 (Conservative)</span>
                                                        <span>Certain threats only</span>
                                                    </span>
                                                </div>
                                            </div>"""

    replacement_slider_1 = """                                                <div class="flex justify-between text-[8px] text-slate-500 font-mono tracking-wide mt-0.5">
                                                    <span class="flex flex-col gap-0.5">
                                                        <span class="font-bold">50 (Aggressive)</span>
                                                        <span>Flags early warnings</span>
                                                    </span>
                                                    <span class="flex flex-col gap-0.5 text-center">
                                                        <span class="font-bold">70 (Balanced)</span>
                                                        <span>Recommended</span>
                                                    </span>
                                                    <span class="flex flex-col gap-0.5 text-right">
                                                        <span class="font-bold">90 (Conservative)</span>
                                                        <span>Certain threats only</span>
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Dynamic Threshold Tuning Toggle */}
                                            <div class="flex items-center justify-between bg-slate-950/40 border border-slate-900/60 p-4 rounded-2xl mt-3">
                                                <div class="flex flex-col gap-0.5">
                                                    <span class="text-[9px] font-black text-slate-200 uppercase tracking-widest font-mono flex items-center gap-1">
                                                        <span class="w-1.5 h-1.5 rounded-full bg-shieldBlue shadow-glowBlue animate-pulse"></span>
                                                        Dynamic Threshold Tuning
                                                    </span>
                                                    <span class="text-[8px] text-slate-500 leading-none">Auto-adjust sensitivity based on active threat events (OTP, Urgency, etc.)</span>
                                                </div>
                                                <button
                                                    onClick={() => setDynamicThresholdEnabled(!dynamicThresholdEnabled)}
                                                    class={`w-10 h-5 rounded-full p-0.5 transition-all duration-300 cursor-pointer ${dynamicThresholdEnabled ? 'bg-shieldBlue' : 'bg-slate-800'}`}
                                                    style={{ border: 'none' }}
                                                >
                                                    <div class={`w-4 h-4 rounded-full bg-white shadow transition-all duration-300 ${dynamicThresholdEnabled ? 'translate-x-5' : 'translate-x-0'}`}></div>
                                                </button>
                                            </div>"""

    if target_slider_1 in content_norm:
        content_norm = content_norm.replace(target_slider_1, replacement_slider_1)
        print("-> Added Settings Slider 1 toggle switch successfully!")
    else:
        print("-> [WARNING] Settings Slider 1 target not found!")

    # Block 2 slider end
    target_slider_2 = """                                            <div class="flex justify-between text-[8px] text-slate-500 font-mono tracking-wide mt-0.5">
                                                <span class="flex flex-col gap-0.5">
                                                    <span class="font-bold">50 (Aggressive)</span>
                                                    <span>Flags early warnings</span>
                                                </span>
                                                <span class="flex flex-col gap-0.5 text-center">
                                                    <span class="font-bold">70 (Balanced)</span>
                                                    <span>Recommended</span>
                                                </span>
                                                <span class="flex flex-col gap-0.5 text-right">
                                                    <span class="font-bold">90 (Conservative)</span>
                                                    <span>Certain threats only</span>
                                                </span>
                                            </div>
                                        </div>"""

    replacement_slider_2 = """                                            <div class="flex justify-between text-[8px] text-slate-500 font-mono tracking-wide mt-0.5">
                                                <span class="flex flex-col gap-0.5">
                                                    <span class="font-bold">50 (Aggressive)</span>
                                                    <span>Flags early warnings</span>
                                                </span>
                                                <span class="flex flex-col gap-0.5 text-center">
                                                    <span class="font-bold">70 (Balanced)</span>
                                                    <span>Recommended</span>
                                                </span>
                                                <span class="flex flex-col gap-0.5 text-right">
                                                    <span class="font-bold">90 (Conservative)</span>
                                                    <span>Certain threats only</span>
                                                </span>
                                            </div>
                                        </div>

                                        {/* Dynamic Threshold Tuning Toggle */}
                                        <div class="flex items-center justify-between bg-slate-950/40 border border-slate-900/60 p-4 rounded-2xl mt-3">
                                            <div class="flex flex-col gap-0.5">
                                                <span class="text-[9px] font-black text-slate-200 uppercase tracking-widest font-mono flex items-center gap-1">
                                                    <span class="w-1.5 h-1.5 rounded-full bg-shieldBlue shadow-glowBlue animate-pulse"></span>
                                                    Dynamic Threshold Tuning
                                                </span>
                                                <span class="text-[8px] text-slate-500 leading-none">Auto-adjust sensitivity based on active threat events (OTP, Urgency, etc.)</span>
                                            </div>
                                            <button
                                                onClick={() => setDynamicThresholdEnabled(!dynamicThresholdEnabled)}
                                                class={`w-10 h-5 rounded-full p-0.5 transition-all duration-300 cursor-pointer ${dynamicThresholdEnabled ? 'bg-shieldBlue' : 'bg-slate-800'}`}
                                                style={{ border: 'none' }}
                                            >
                                                <div class={`w-4 h-4 rounded-full bg-white shadow transition-all duration-300 ${dynamicThresholdEnabled ? 'translate-x-5' : 'translate-x-0'}`}></div>
                                            </button>
                                        </div>"""

    if target_slider_2 in content_norm:
        content_norm = content_norm.replace(target_slider_2, replacement_slider_2)
        print("-> Added Settings Slider 2 toggle switch successfully!")
    else:
        print("-> [WARNING] Settings Slider 2 target not found!")

    # 5. Speaker Mode Risk Classifier Header and Score Bar
    target_speaker_status = """                                        <div class="flex justify-between items-center bg-slate-950 border border-darkBorder/40 p-4 rounded-xl">
                                            <div>
                                                <span class="text-[9px] font-bold text-slate-500 uppercase tracking-wider block font-black">Risk Status</span>
                                                <span class={`text-sm font-black uppercase tracking-wider ${
                                                    speakerScore >= 70 ? 'text-shieldRed' : speakerScore >= 40 ? 'text-shieldOrange' : 'text-shieldGreen'
                                                }`}>
                                                    {speakerRiskLevel}
                                                </span>
                                            </div>
                                            <div class="text-right">
                                                <span class="text-[9px] font-bold text-slate-500 uppercase tracking-wider block font-black">AI Score</span>
                                                <span class={`text-2xl font-black font-mono tracking-tighter ${
                                                    speakerScore >= 70 ? 'text-shieldRed' : speakerScore >= 40 ? 'text-shieldOrange' : 'text-shieldGreen'
                                                }`}>
                                                    {speakerScore}%
                                                </span>
                                            </div>
                                        </div>

                                        {/* Score Bar */}
                                        <div class="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-900">
                                            <div 
                                                class={`h-full transition-all duration-300 ${
                                                    speakerScore >= 70 ? 'bg-shieldRed' : speakerScore >= 40 ? 'bg-shieldOrange' : 'bg-shieldGreen'
                                                }`}
                                                style={{ width: `${speakerScore}%` }}
                                            ></div>
                                        </div>"""

    replacement_speaker_status = """                                        <div class="flex justify-between items-center bg-slate-950 border border-darkBorder/40 p-4 rounded-xl">
                                            <div>
                                                <span class="text-[9px] font-bold text-slate-500 uppercase tracking-wider block font-black">Risk Status</span>
                                                <span class={`text-sm font-black uppercase tracking-wider ${
                                                    speakerScore >= speakerDynamicThreshold ? 'text-shieldRed' : speakerScore >= 40 ? 'text-shieldOrange' : 'text-shieldGreen'
                                                }`}>
                                                    {speakerRiskLevel}
                                                </span>
                                            </div>
                                            <div class="text-right">
                                                <span class="text-[9px] font-bold text-slate-500 uppercase tracking-wider block font-black text-slate-400">
                                                    {dynamicThresholdEnabled ? 'Adaptive Threshold' : 'Static Threshold'} ({speakerDynamicThreshold}%)
                                                </span>
                                                <span class={`text-2xl font-black font-mono tracking-tighter ${
                                                    speakerScore >= speakerDynamicThreshold ? 'text-shieldRed' : speakerScore >= 40 ? 'text-shieldOrange' : 'text-shieldGreen'
                                                }`}>
                                                    {speakerScore}%
                                                </span>
                                            </div>
                                        </div>

                                        {/* Score Bar */}
                                        <div class="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-900">
                                            <div 
                                                class={`h-full transition-all duration-300 ${
                                                    speakerScore >= speakerDynamicThreshold ? 'bg-shieldRed' : speakerScore >= 40 ? 'bg-shieldOrange' : 'bg-shieldGreen'
                                                }`}
                                                style={{ width: `${speakerScore}%` }}
                                            ></div>
                                        </div>"""

    if target_speaker_status in content_norm:
        content_norm = content_norm.replace(target_speaker_status, replacement_speaker_status)
        print("-> Updated Speaker Mode risk classifier & score bar successfully!")
    else:
        print("-> [WARNING] Speaker Mode risk classifier target not found!")

    # 6. Speaker Mode Mitigations Ternary
    target_speaker_mitigation = """                                        {/* Threat alert mitigations */}
                                        {speakerScore >= 70 ? (
                                            <div class="p-3 bg-shieldRed/10 border border-shieldRed/30 rounded-xl flex flex-col gap-2.5 animate-pulse">
                                                <div class="flex items-center gap-2">
                                                    <span class="text-lg">🚨</span>
                                                    <span class="text-xs font-black text-shieldRed uppercase tracking-wider">CRITICAL THREAT FLAG</span>
                                                </div>
                                                <p class="text-[10px] text-slate-400 leading-relaxed font-semibold">
                                                    <strong>Recommendation:</strong> Hang up immediately. Caller matches impersonation threat patterns.
                                                </p>
                                                <div class="flex gap-2 justify-end mt-1">
                                                    <button onClick={stopSpeakerListening} class="px-3 py-1.5 bg-shieldRed hover:bg-shieldRed/80 text-white text-[10px] font-extrabold rounded-lg border-none transition-all cursor-pointer">
                                                        Hang Up Call
                                                    </button>
                                                    <button onClick={handleSaveSpeakerIncident} class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold rounded-lg border-none transition-all cursor-pointer">
                                                        Log Incident
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div class="p-3 bg-slate-900/60 border border-darkBorder/40 rounded-xl flex items-center gap-2">
                                                <span class="text-base text-shieldGreen">🛡️</span>
                                                <span class="text-[10px] text-slate-400 font-medium font-semibold">Acoustic Shield status normal. Listening for risk triggers...</span>
                                            </div>
                                        )}"""

    replacement_speaker_mitigation = """                                        {/* Adaptive Threshold Tuning Engine Details (Speaker Mode) */}
                                        {dynamicThresholdEnabled && (
                                            <div class="flex flex-col gap-1.5 bg-slate-950/50 p-2.5 rounded-xl border border-slate-900/80 mb-3">
                                                <div class="flex justify-between items-center text-[9px] font-bold text-slate-400">
                                                    <span>⚡ ADAPTIVE THRESHOLD TUNING ENGINE</span>
                                                    <span class="font-mono text-slate-300">Active: {speakerDynamicThreshold}% (Base: {detectionSensitivity}%)</span>
                                                </div>
                                                <div class="flex flex-wrap gap-2 text-[8px] font-mono leading-none">
                                                    <span class="text-slate-400">-5% (Unknown Caller)</span>
                                                    {speakerBadges.otpRequest && <span class="text-shieldRed font-bold">-20% (OTP Verification Block)</span>}
                                                    {speakerBadges.moneyTransfer && <span class="text-shieldRed font-bold">-15% (Financial Transfer)</span>}
                                                    {speakerBadges.urgencyDetected && <span class="text-shieldOrange">-10% (Urgency Language)</span>}
                                                    {speakerBadges.possibleSyntheticSpeech && <span class="text-shieldRed font-bold animate-pulse">-25% (Synthetic Voice Cloned)</span>}
                                                    {!speakerBadges.otpRequest && !speakerBadges.moneyTransfer && !speakerBadges.urgencyDetected && !speakerBadges.possibleSyntheticSpeech && <span class="text-slate-600">Waiting for risk triggers...</span>}
                                                </div>
                                            </div>
                                        )}

                                        {/* Threat alert mitigations */}
                                        {speakerScore >= speakerDynamicThreshold ? (
                                            <div class="p-3 bg-shieldRed/10 border border-shieldRed/30 rounded-xl flex flex-col gap-2.5 animate-pulse">
                                                <div class="flex items-center gap-2">
                                                    <span class="text-lg">🚨</span>
                                                    <span class="text-xs font-black text-shieldRed uppercase tracking-wider">CRITICAL THREAT FLAG</span>
                                                </div>
                                                <p class="text-[10px] text-slate-400 leading-relaxed font-semibold">
                                                    <strong>Recommendation:</strong> Hang up immediately. Caller matches impersonation threat patterns.
                                                </p>
                                                <div class="flex gap-2 justify-end mt-1">
                                                    <button onClick={stopSpeakerListening} class="px-3 py-1.5 bg-shieldRed hover:bg-shieldRed/80 text-white text-[10px] font-extrabold rounded-lg border-none transition-all cursor-pointer">
                                                        Hang Up Call
                                                    </button>
                                                    <button onClick={handleSaveSpeakerIncident} class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold rounded-lg border-none transition-all cursor-pointer">
                                                        Log Incident
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div class="p-3 bg-slate-900/60 border border-darkBorder/40 rounded-xl flex items-center gap-2">
                                                <span class="text-base text-shieldGreen">🛡️</span>
                                                <span class="text-[10px] text-slate-400 font-medium font-semibold">Acoustic Shield status normal. Listening for risk triggers...</span>
                                            </div>
                                        )}"""

    if target_speaker_mitigation in content_norm:
        content_norm = content_norm.replace(target_speaker_mitigation, replacement_speaker_mitigation)
        print("-> Updated Speaker Mode mitigations successfully!")
    else:
        print("-> [WARNING] Speaker Mode mitigations target not found!")

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content_norm)

def patch_backend_main_py(file_path):
    print(f"Patching {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Inject calculate_dynamic_threshold helper before _process_audio_chunk
    target_main_helpers = """async def _process_audio_chunk("""

    replacement_main_helpers = """def calculate_dynamic_threshold(base_threshold: float, text: str, voice_label: str, rep_data: dict, risk_factors: list) -> float:
    # base_threshold is a fraction (e.g. 0.71)
    val = base_threshold
    
    # Base Unknown caller deduction
    val -= 0.05
    
    text_lower = text.lower()
    
    # Impersonation Attempt
    has_impersonation = any(f.get("indicator") == "Identity Claim Verification" for f in risk_factors)
    if has_impersonation:
        val -= 0.10
        
    # Urgency Language
    has_urgency = any("Urgent" in f.get("evidence", "") for f in risk_factors) or any(p in text_lower for p in ["immediately", "avoid arrest", "jail", "within 2 hours", "account block", "immediately block", "urgent", "urgently"])
    if has_urgency:
        val -= 0.10
        
    # Verification Request (OTP)
    has_otp = any("OTP" in f.get("evidence", "") for f in risk_factors) or any(p in text_lower for p in ["otp", "one time password", "verification code", "digits sent", "pin code", "share your code"])
    if has_otp:
        val -= 0.20
        
    # Money Request
    has_money = any(p in text_lower for p in ["paise", "rupees", "money", "upi", "transfer", "deposit", "fee", "payment", "pay", "bills"])
    if has_money:
        val -= 0.15
        
    # Synthetic Voice Indicators
    if voice_label == "synthetic":
        val -= 0.25
        
    # Return as fraction (clip between 0.30 and 0.95)
    return max(0.30, min(0.95, val))


async def _process_audio_chunk("""

    content_norm = content.replace("\r\n", "\n")

    if target_main_helpers in content_norm:
        content_norm = content_norm.replace(target_main_helpers, replacement_main_helpers)
        print("-> Injected calculate_dynamic_threshold successfully!")
    else:
        print("-> [WARNING] _process_audio_chunk not found in main.py!")

    # 2. Update dynamic_threshold calculation inside _process_audio_chunk
    target_main_process = """    # 2b. Compute explainable threat score from all indicators (Text, Voice, Reputation, Impersonation)
    xai_result = analyze_xai_threat(rolling_text, voice_label, voice_score, rep_data, from_num, db)
    score = xai_result["fraud_score"]
    label = xai_result["risk_label"]

    print(f"[AI] call={call_sid} score={score:.3f} label={label} voice={voice_label} reputation={rep_data['reputation_label']} | '{text[:60]}'")"""

    replacement_main_process = """    # 2b. Compute explainable threat score from all indicators (Text, Voice, Reputation, Impersonation)
    xai_result = analyze_xai_threat(rolling_text, voice_label, voice_score, rep_data, from_num, db)
    score = xai_result["fraud_score"]
    label = xai_result["risk_label"]
    
    # Compute dynamic threshold
    dynamic_threshold = calculate_dynamic_threshold(threshold, rolling_text, voice_label, rep_data, xai_result["risk_factors"])

    print(f"[AI] call={call_sid} score={score:.3f} label={label} voice={voice_label} reputation={rep_data['reputation_label']} threshold={dynamic_threshold:.3f} | '{text[:60]}'")"""

    if target_main_process in content_norm:
        content_norm = content_norm.replace(target_main_process, replacement_main_process)
        print("-> Injected dynamic threshold computation inside _process_audio_chunk successfully!")
    else:
        print("-> [WARNING] analyze_xai_threat call not found inside main.py!")

    # 3. Add dynamic_threshold to SSE payload
    target_main_sse = """    # 4. Broadcast rich XAI response to SSE queue
    q = live_queues.get(call_sid)
    if q and not q.full():
        await q.put({
            "score": score, 
            "label": label, 
            "transcript": text,
            "voice_label": voice_label,
            "voice_score": voice_score,
            "reputation_flags": rep_data["flag_count"],
            "risk_factors": xai_result["risk_factors"],
            "mitigation_advice": xai_result["mitigation_advice"]
        })"""

    replacement_main_sse = """    # 4. Broadcast rich XAI response to SSE queue
    q = live_queues.get(call_sid)
    if q and not q.full():
        await q.put({
            "score": score, 
            "label": label, 
            "transcript": text,
            "voice_label": voice_label,
            "voice_score": voice_score,
            "reputation_flags": rep_data["flag_count"],
            "risk_factors": xai_result["risk_factors"],
            "mitigation_advice": xai_result["mitigation_advice"],
            "dynamic_threshold": round(dynamic_threshold * 100, 1)
        })"""

    if target_main_sse in content_norm:
        content_norm = content_norm.replace(target_main_sse, replacement_main_sse)
        print("-> Added dynamic_threshold to SSE broadcast successfully!")
    else:
        print("-> [WARNING] SSE broadcast block not found inside main.py!")

    # 4. Update the warning checks to use dynamic_threshold
    target_main_action = """    # 5. Take action
    if not warning_sent:
        if label == "fraud" and score >= threshold:"""

    replacement_main_action = """    # 5. Take action
    if not warning_sent:
        if label == "fraud" and score >= dynamic_threshold:"""

    if target_main_action in content_norm:
        content_norm = content_norm.replace(target_main_action, replacement_main_action)
        print("-> Updated Twilio Warning trigger checks to use dynamic threshold successfully!")
    else:
        print("-> [WARNING] Take action check block not found inside main.py!")

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content_norm)

if __name__ == "__main__":
    patch_demo_html("demo.html")
    patch_backend_demo_html(os.path.join("backend", "demo.html"))
    patch_backend_main_py(os.path.join("backend", "main.py"))
    print("All patching operations completed!")
