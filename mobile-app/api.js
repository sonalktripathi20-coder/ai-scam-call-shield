// api.js - All backend API calls centralized here

import axios from "axios";

// ─── CHANGE THIS to your ngrok URL or deployed server URL ───────────────────
export const BASE_URL = "https://slick-emus-hammer.loca.lt";
// ─────────────────────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// ── Calls ─────────────────────────────────────────────────────────────────────

export const fetchCalls = async (limit = 50) => {
  const { data } = await api.get(`/api/calls?limit=${limit}`);
  return data;
};

export const fetchCallDetail = async (callSid) => {
  const { data } = await api.get(`/api/calls/${callSid}`);
  return data;
};

// ── Stats ─────────────────────────────────────────────────────────────────────

export const fetchStats = async () => {
  const { data } = await api.get("/api/stats");
  return data;
};

// ── Settings ──────────────────────────────────────────────────────────────────

export const fetchSettings = async () => {
  const { data } = await api.get("/api/settings");
  return data;
};

export const updateSettings = async (settings) => {
  const { data } = await api.post("/api/settings", settings);
  return data;
};

// ── Health Check ──────────────────────────────────────────────────────────────

export const checkHealth = async () => {
  try {
    const { data } = await api.get("/health");
    return { online: true, ...data };
  } catch {
    return { online: false };
  }
};

// ── SSE: Live Risk Score Subscription ────────────────────────────────────────
// React Native doesn't natively support EventSource, we use polling fallback.
// For production, install: react-native-event-source

// ── Contacts ──────────────────────────────────────────────────────────────────

export const syncContacts = async (contacts) => {
  const { data } = await api.post("/api/contacts/sync", { contacts });
  return data;
};

export const fetchContactsCount = async () => {
  const { data } = await api.get("/api/contacts/count");
  return data;
};

// ── Push Token ────────────────────────────────────────────────────────────────

export const registerPushToken = async (token) => {
  const { data } = await api.post("/api/push/register", { token });
  return data;
};

// ── Decline Call ──────────────────────────────────────────────────────────────

export const declineCall = async (callSid) => {
  const { data } = await api.post(`/api/calls/${callSid}/decline`);
  return data;
};

// ── Active Calls ──────────────────────────────────────────────────────────────

export const fetchActiveCalls = async () => {
  const { data } = await api.get("/api/calls/active");
  return data;
};
export const subscribeToLiveScore = (callSid, onData, onError) => {
  let running = true;
  let lastTranscript = "";

  const poll = async () => {
    while (running) {
      try {
        const { data } = await api.get(`/api/calls/${callSid}`);
        if (data) {
          const score = data.final_score ?? 0;
          const label = data.risk_label ?? "safe";
          const scoreEvents = data.score_events ?? [];
          const lastEvent = scoreEvents.length > 0 ? scoreEvents[scoreEvents.length - 1] : null;
          const transcript = lastEvent ? lastEvent.transcript_chunk : "";

          // Only invoke callback if we got valid data
          onData({
            score,
            label,
            transcript
          });
        }
      } catch (e) {
        // Call ended or not active
        if (e?.response?.status === 404) running = false;
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
  };

  poll().catch(onError);

  return () => {
    running = false;
  };
};

