// screens/LiveCallScreen.js
// Auto-pops when an unknown call is being monitored.
// Shows real-time risk meter + Decline button.

import React, { useState, useEffect, useRef } from "react";
import {
  View, Text, StyleSheet, TouchableOpacity,
  Animated, Vibration, Alert, Dimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { COLORS } from "../App";
import { declineCall, subscribeToLiveScore } from "../api";

const { width, height } = Dimensions.get("window");

export default function LiveCallScreen({ route, navigation }) {
  const { callSid, fromNumber } = route.params || {};
  const [score, setScore]       = useState(0);
  const [label, setLabel]       = useState("safe");
  const [transcript, setTranscript] = useState([]);
  const [elapsed, setElapsed]   = useState(0);
  const [declining, setDeclining] = useState(false);

  const pulseAnim  = useRef(new Animated.Value(1)).current;
  const scoreAnim  = useRef(new Animated.Value(0)).current;
  const timerRef   = useRef(null);
  const pollRef    = useRef(null);

  const color = label === "fraud"
    ? COLORS.fraud
    : label === "suspicious"
    ? COLORS.suspicious
    : COLORS.safe;

  // ── Pulse animation ────────────────────────
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.12, duration: 700, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1.0,  duration: 700, useNativeDriver: true }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  // ── Animate score bar ──────────────────────
  useEffect(() => {
    Animated.spring(scoreAnim, {
      toValue: score,
      friction: 5,
      useNativeDriver: false,
    }).start();
    // Vibrate on fraud detection
    if (label === "fraud") Vibration.vibrate([0, 300, 200, 300]);
  }, [score, label]);

  // ── Timer ──────────────────────────────────
  useEffect(() => {
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  // ── Poll live score from backend ───────────
  useEffect(() => {
    if (!callSid) return;
    const unsubscribe = subscribeToLiveScore(
      callSid,
      (data) => {
        setScore(data.score);
        setLabel(data.label);
        if (data.transcript) {
          setTranscript(prev => {
            // Avoid duplicating the last chunk if it hasn't changed
            if (prev.length > 0 && prev[prev.length - 1] === data.transcript) {
              return prev;
            }
            return [...prev.slice(-6), data.transcript];
          });
        }
      },
      (err) => {
        console.warn("[LiveCall] Polling error:", err);
      }
    );
    return unsubscribe;
  }, [callSid]);


  const formatTime = s => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;

  const handleDecline = () => {
    Alert.alert(
      "Decline Call?",
      "This will immediately disconnect the unknown caller.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Decline Now",
          style: "destructive",
          onPress: async () => {
            setDeclining(true);
            try {
              await declineCall(callSid);
            } catch {}
            navigation.goBack();
          },
        },
      ]
    );
  };

  const barWidth = scoreAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
    extrapolate: "clamp",
  });

  return (
    <View style={[styles.container, label === "fraud" && styles.fraudBg]}>

      {/* ── Header ── */}
      <View style={styles.header}>
        <Animated.View style={[styles.dot, { backgroundColor: color, transform: [{ scale: pulseAnim }] }]} />
        <Text style={styles.headerText}>UNKNOWN CALLER — AI MONITORING</Text>
        <Text style={styles.timer}>{formatTime(elapsed)}</Text>
      </View>

      {/* ── Number ── */}
      <Text style={styles.number}>{fromNumber || "Unknown Number"}</Text>
      <Text style={styles.numberSub}>Not in your contacts</Text>

      {/* ── Big Risk Gauge ── */}
      <View style={[styles.gaugeOuter, { borderColor: color + "55" }]}>
        <View style={[styles.gaugeInner, { borderColor: color }]}>
          <Text style={[styles.gaugePct, { color }]}>{Math.round(score * 100)}%</Text>
          <Text style={styles.gaugeSub}>Risk Score</Text>
        </View>
      </View>

      {/* Status label */}
      <View style={[styles.statusBadge, { backgroundColor: color + "22", borderColor: color + "55" }]}>
        <Text style={[styles.statusText, { color }]}>
          {label === "fraud" ? "🚨 HIGH FRAUD RISK"
           : label === "suspicious" ? "⚠️  SUSPICIOUS CALLER"
           : "✅  CALL APPEARS SAFE"}
        </Text>
      </View>

      {/* ── Progress Bar ── */}
      <View style={styles.barTrack}>
        <Animated.View style={[styles.barFill, { width: barWidth, backgroundColor: color }]} />
        <View style={[styles.barMark, { left: "40%" }]} />
        <View style={[styles.barMark, { left: "70%" }]} />
      </View>
      <View style={styles.barLabels}>
        <Text style={styles.barLabel}>Safe</Text>
        <Text style={styles.barLabel}>0.4</Text>
        <Text style={styles.barLabel}>0.7</Text>
        <Text style={styles.barLabel}>Fraud</Text>
      </View>

      {/* ── Live Transcript ── */}
      <View style={styles.transcriptBox}>
        <Text style={styles.transcriptTitle}>📝 Live Transcript</Text>
        {transcript.length === 0
          ? <Text style={styles.transcriptEmpty}>Listening to call...</Text>
          : transcript.map((t, i) => (
            <Text key={i} style={styles.transcriptLine}>• {t}</Text>
          ))
        }
      </View>

      {/* ── Action Buttons ── */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.btnDecline, declining && { opacity: 0.5 }]}
          onPress={handleDecline}
          disabled={declining}
          activeOpacity={0.8}
        >
          <Ionicons name="call" size={22} color="#fff" style={{ transform: [{ rotate: "135deg" }] }} />
          <Text style={styles.btnDeclineText}>
            {declining ? "Declining..." : "Decline Call"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.btnBack}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.btnBackText}>← Back to Dashboard</Text>
        </TouchableOpacity>
      </View>

      {/* ── Recommendation Box ── */}
      {label !== "safe" && (
        <View style={[styles.recommendation, { borderColor: color }]}>
          <Ionicons name="information-circle" size={18} color={color} />
          <Text style={[styles.recText, { color }]}>
            {label === "fraud"
              ? "Do NOT share OTP, UPI PIN, Aadhaar, or bank details. Decline immediately!"
              : "Be careful. Do not share any personal or financial information."}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, padding: 24, alignItems: "center" },
  fraudBg:   { backgroundColor: "#110008" },

  header:     { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12, width: "100%" },
  dot:        { width: 10, height: 10, borderRadius: 5 },
  headerText: { color: COLORS.textMuted, fontSize: 12, fontWeight: "700", letterSpacing: 1, flex: 1 },
  timer:      { color: COLORS.text, fontSize: 14, fontWeight: "600" },

  number:    { fontSize: 32, fontWeight: "800", color: COLORS.text, marginBottom: 4 },
  numberSub: { color: COLORS.textMuted, fontSize: 13, marginBottom: 28 },

  gaugeOuter: { width: 200, height: 200, borderRadius: 100, borderWidth: 10, justifyContent: "center", alignItems: "center", marginBottom: 16 },
  gaugeInner: { width: 168, height: 168, borderRadius: 84, borderWidth: 4, backgroundColor: COLORS.bg, justifyContent: "center", alignItems: "center" },
  gaugePct:   { fontSize: 46, fontWeight: "900" },
  gaugeSub:   { color: COLORS.textMuted, fontSize: 13 },

  statusBadge: { borderRadius: 24, paddingHorizontal: 20, paddingVertical: 8, borderWidth: 1, marginBottom: 20 },
  statusText:  { fontSize: 15, fontWeight: "800", letterSpacing: 0.5 },

  barTrack:  { width: "100%", height: 10, backgroundColor: COLORS.border, borderRadius: 5, overflow: "visible", marginBottom: 4, position: "relative" },
  barFill:   { height: "100%", borderRadius: 5 },
  barMark:   { position: "absolute", top: -2, width: 2, height: 14, backgroundColor: COLORS.bg + "99" },
  barLabels: { flexDirection: "row", justifyContent: "space-between", width: "100%", marginBottom: 16 },
  barLabel:  { color: COLORS.textMuted, fontSize: 10 },

  transcriptBox:   { width: "100%", backgroundColor: COLORS.surface, borderRadius: 14, padding: 14, marginBottom: 20, minHeight: 80, borderWidth: 1, borderColor: COLORS.border },
  transcriptTitle: { color: COLORS.textMuted, fontSize: 12, fontWeight: "700", marginBottom: 8 },
  transcriptEmpty: { color: COLORS.textMuted, fontSize: 13, fontStyle: "italic" },
  transcriptLine:  { color: COLORS.text, fontSize: 12, lineHeight: 20 },

  actions:       { width: "100%", gap: 10, marginBottom: 16 },
  btnDecline:    { backgroundColor: COLORS.fraud, borderRadius: 16, paddingVertical: 16, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10 },
  btnDeclineText:{ color: "#fff", fontSize: 18, fontWeight: "800" },
  btnBack:       { borderRadius: 16, paddingVertical: 12, alignItems: "center", borderWidth: 1, borderColor: COLORS.border },
  btnBackText:   { color: COLORS.textMuted, fontSize: 14 },

  recommendation: { flexDirection: "row", gap: 10, alignItems: "flex-start", backgroundColor: COLORS.surface, borderRadius: 12, padding: 12, borderWidth: 1, width: "100%" },
  recText:        { flex: 1, fontSize: 12, lineHeight: 18 },
});
