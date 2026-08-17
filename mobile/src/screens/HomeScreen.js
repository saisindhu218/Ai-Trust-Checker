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
import { analyzeText } from "../services/api";
import ResultCard from "../components/ResultCard";

export default function HomeScreen() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

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
          <Text style={styles.title}>AI Trust Checker</Text>
          <Text style={styles.subtitle}>Before you click, pay, share, or believe — check it.</Text>

          <TextInput
            style={styles.input}
            multiline
            placeholder="Paste a suspicious SMS, WhatsApp, or email message here..."
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

          {result && <ResultCard result={result} />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#F1F5F9" },
  scroll: { padding: 20, paddingBottom: 60 },
  title: { fontSize: 26, fontWeight: "800", color: "#0F172A" },
  subtitle: { fontSize: 14, color: "#64748B", marginTop: 4, marginBottom: 20 },
  input: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 14,
    minHeight: 120,
    textAlignVertical: "top",
    fontSize: 15,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  button: {
    backgroundColor: "#0F172A",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 14,
  },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 15, letterSpacing: 1 },
});
