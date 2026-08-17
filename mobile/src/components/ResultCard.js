import React from "react";
import { View, Text, StyleSheet } from "react-native";

const LEVEL_COLORS = {
  HIGH: "#DC2626",
  MEDIUM: "#D97706",
  LOW: "#16A34A",
};

export default function ResultCard({ result }) {
  const color = LEVEL_COLORS[result.risk_level] || "#64748B";

  return (
    <View style={styles.card}>
      <View style={[styles.scoreBox, { borderColor: color }]}>
        <Text style={[styles.scoreText, { color }]}>{result.risk_score}/100</Text>
        <Text style={[styles.levelText, { color }]}>{result.risk_level} RISK</Text>
        <Text style={styles.categoryText}>{result.category}</Text>
      </View>

      {!!result.summary && <Text style={styles.summary}>{result.summary}</Text>}

      {result.red_flags.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Why we flagged this</Text>
          {result.red_flags.map((flag, i) => (
            <Text key={i} style={styles.flagItem}>⚠ {flag}</Text>
          ))}
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What you should do</Text>
        {result.recommended_actions.map((a, i) => (
          <Text key={i} style={styles.actionItem}>{i + 1}. {a}</Text>
        ))}
      </View>

      <View style={styles.footerRow}>
        <Text style={styles.footerText}>Confidence: {result.confidence.toUpperCase()}</Text>
        <Text style={styles.footerText}>
          {result.ai_used ? "AI-assisted" : "Rule-based only"}
        </Text>
      </View>
      {result.ai_error && (
        <Text style={styles.warnText}>AI reasoning unavailable ({result.ai_error}). Showing rule-based result only.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 18,
    marginTop: 16,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  scoreBox: {
    alignItems: "center",
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 16,
    marginBottom: 16,
  },
  scoreText: { fontSize: 32, fontWeight: "800" },
  levelText: { fontSize: 16, fontWeight: "700", marginTop: 4, letterSpacing: 1 },
  categoryText: { fontSize: 13, color: "#475569", marginTop: 4 },
  summary: { fontSize: 14, color: "#334155", marginBottom: 14, lineHeight: 20 },
  section: { marginBottom: 14 },
  sectionTitle: { fontSize: 13, fontWeight: "700", color: "#0F172A", marginBottom: 6, textTransform: "uppercase" },
  flagItem: { fontSize: 14, color: "#B91C1C", marginBottom: 4 },
  actionItem: { fontSize: 14, color: "#0F172A", marginBottom: 4 },
  footerRow: { flexDirection: "row", justifyContent: "space-between", marginTop: 6 },
  footerText: { fontSize: 12, color: "#64748B" },
  warnText: { fontSize: 12, color: "#B45309", marginTop: 8 },
});
