import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { analyzeText } from "../services/api";
import ResultCard from "../components/ResultCard";

export default function HomeScreen() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [isDark, setIsDark] = useState(false);

  const styles = getStyles(isDark);

  const handleCheck = async () => {
    if (!text.trim()) {
      Alert.alert("Nothing to check", "Paste a message first.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeText(text.trim());
      setResult(data);
    } catch (err) {
      Alert.alert(
        "Couldn't reach the server",
        "Make sure the backend is running and API_BASE_URL in src/services/api.js matches your laptop's IP. " +
          "If it still hangs, check Windows Firewall isn't blocking port 8000.\n\n" +
          err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>AI Trust Checker</Text>
              <Text style={styles.subtitle}>Before you click, pay, share, or believe — check it.</Text>
            </View>
            <TouchableOpacity
              style={styles.themeToggle}
              onPress={() => setIsDark((prev) => !prev)}
              accessibilityLabel={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              <Ionicons
                name={isDark ? "sunny" : "moon"}
                size={20}
                color={isDark ? "#FDE68A" : "#0F172A"}
              />
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.input}
            multiline
            placeholder="Paste a suspicious SMS, WhatsApp, or email message here..."
            placeholderTextColor={isDark ? "#64748B" : "#94A3B8"}
            value={text}
            onChangeText={setText}
          />

          <TouchableOpacity style={styles.button} onPress={handleCheck} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>CHECK NOW</Text>
            )}
          </TouchableOpacity>

          {result && <ResultCard result={result} isDark={isDark} />}

          <View style={styles.divider} />
          <Text style={styles.credit}>AI Trust Checker · Built by Sai Sindhu Rachabattuni</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function getStyles(isDark) {
  const bg = isDark ? "#0F172A" : "#F1F5F9";
  const cardBg = isDark ? "#1E293B" : "#fff";
  const textPrimary = isDark ? "#F1F5F9" : "#0F172A";
  const textSecondary = isDark ? "#94A3B8" : "#64748B";
  const border = isDark ? "#334155" : "#E2E8F0";

  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: bg },
    scroll: { padding: 20, paddingBottom: 60 },
    headerRow: {
      flexDirection: "row",
      alignItems: "flex-start",
      justifyContent: "space-between",
      marginBottom: 20,
    },
    title: { fontSize: 26, fontWeight: "800", color: textPrimary },
    subtitle: { fontSize: 14, color: textSecondary, marginTop: 4 },
    themeToggle: {
      width: 36,
      height: 36,
      borderRadius: 18,
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: cardBg,
      borderWidth: 1,
      borderColor: border,
      marginLeft: 12,
    },
    input: {
      backgroundColor: cardBg,
      borderRadius: 12,
      padding: 14,
      minHeight: 120,
      textAlignVertical: "top",
      fontSize: 15,
      borderWidth: 1,
      borderColor: border,
      color: textPrimary,
    },
    button: {
      backgroundColor: isDark ? "#F1F5F9" : "#0F172A",
      borderRadius: 12,
      paddingVertical: 14,
      alignItems: "center",
      marginTop: 14,
    },
    buttonText: {
      color: isDark ? "#0F172A" : "#fff",
      fontWeight: "700",
      fontSize: 15,
      letterSpacing: 1,
    },
    divider: { height: 1, backgroundColor: border, marginTop: 32, marginBottom: 16 },
    credit: { fontSize: 12, color: textSecondary, textAlign: "center" },
  });
}