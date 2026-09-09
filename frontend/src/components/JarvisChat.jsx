import { useEffect, useRef, useState } from "react";

export default function JarvisChat({
  messages,
  onSendMessage,
  isProcessing,
  connectionStatus,
}) {
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [speechError, setSpeechError] = useState(null);
  const [voiceMuted, setVoiceMuted] = useState(false);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);
  const lastSpokenIdRef = useRef(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  // Expose speaker for latest assistant message
  useEffect(() => {
    if (messages.length === 0) return;
    const latest = messages[messages.length - 1];
    if (
      latest.role === "assistant" &&
      latest.id !== lastSpokenIdRef.current &&
      latest.content
    ) {
      lastSpokenIdRef.current = latest.id;
      if (!voiceMuted && window.speechSynthesis) {
        try {
          window.speechSynthesis.cancel();
          const clean = latest.content.replace(/[*#_`]/g, "");
          const utterance = new SpeechSynthesisUtterance(clean);
          utterance.rate = 0.95;
          utterance.pitch = 1.0;
          window.speechSynthesis.speak(utterance);
        } catch {
          // ignore synthesis error
        }
      }
    }
  }, [messages, voiceMuted]);

  // Web Speech API
  const toggleListening = () => {
    setSpeechError(null);

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechError("Speech recognition is not supported in this browser.");
      setTimeout(() => setSpeechError(null), 4000);
      return;
    }

    if (listening) {
      try {
        recognitionRef.current?.stop();
      } catch {
        // ignore
      }
      setListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onstart = () => {
        setListening(true);
        setSpeechError(null);
      };

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((res) => res[0].transcript)
          .join("");
        setInput(transcript);

        if (event.results[0].isFinal) {
          setListening(false);
          if (transcript.trim()) {
            handleSubmitText(transcript.trim());
          }
        }
      };

      recognition.onerror = (event) => {
        setListening(false);
        if (event.error !== "aborted") {
          setSpeechError(`Voice error: ${event.error}`);
          setTimeout(() => setSpeechError(null), 4000);
        }
      };

      recognition.onend = () => {
        setListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setListening(false);
      setSpeechError("Microphone access failed.");
      setTimeout(() => setSpeechError(null), 4000);
    }
  };

  const handleSubmitText = (textToSend) => {
    const query = (textToSend !== undefined ? textToSend : input).trim();
    if (!query || isProcessing) return;
    setInput("");
    onSendMessage(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmitText();
    }
  };

  return (
    <section className="jarvis-console" aria-label="JARVIS AI Command Center">
      {/* HEADER */}
      <div className="console-head">
        <div className="console-brand">
          <div className="console-indicator-dot"></div>
          <span className="console-title">JARVIS INTELLIGENCE</span>
        </div>

        <div className="console-controls">
          <button
            type="button"
            className={`console-voice-toggle ${voiceMuted ? "muted" : ""}`}
            onClick={() => setVoiceMuted(!voiceMuted)}
            title={voiceMuted ? "Voice synthesis muted (click to unmute)" : "Voice synthesis active (click to mute)"}
            aria-label={voiceMuted ? "Unmute voice synthesis" : "Mute voice synthesis"}
          >
            {voiceMuted ? "🔇 Voice Muted" : "🔊 Voice Active"}
          </button>

          <span
            className={`console-status-badge ${
              connectionStatus === "ONLINE"
                ? "status-ready"
                : connectionStatus === "RECONNECTING"
                ? "status-warn"
                : "status-offline"
            }`}
          >
            ● {connectionStatus === "ONLINE" ? "AI ACTIVE" : connectionStatus === "RECONNECTING" ? "RECONNECTING" : "BACKEND OFFLINE"}
          </span>
        </div>
      </div>

      {/* CONVERSATION STREAM */}
      <div className="console-stream" role="log" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`console-message message-${msg.role} ${msg.type ? `type-${msg.type}` : ""}`}
          >
            <div className="message-header">
              <span className="message-author">
                {msg.role === "user" ? "DEFENDER" : msg.role === "system" ? "SYSTEM" : "JARVIS"}
              </span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-body">{msg.content}</div>
          </div>
        ))}

        {isProcessing && (
          <div className="console-message message-assistant processing">
            <div className="message-header">
              <span className="message-author">JARVIS</span>
              <span className="message-time">Just now</span>
            </div>
            <div className="message-body">
              <span className="thinking-pulse">● ● ●</span> Analyzing telemetry & query...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* SPEECH ERROR BANNER */}
      {speechError && (
        <div className="speech-error-bar" role="alert">
          ⚠ {speechError}
        </div>
      )}

      {/* COMPOSER */}
      <div className={`console-composer ${listening ? "composer-listening" : ""}`}>
        {listening && (
          <div className="listening-bar" aria-live="assertive">
            <span className="rec-dot">●</span>
            <span className="rec-text">Listening... speak now</span>
            <button
              type="button"
              className="rec-cancel-btn"
              onClick={toggleListening}
              aria-label="Stop listening"
            >
              Cancel
            </button>
          </div>
        )}

        <div className="composer-input-row">
          <textarea
            ref={textareaRef}
            className="composer-textarea"
            rows="1"
            placeholder={
              connectionStatus === "OFFLINE"
                ? "Backend offline. Commands disabled until reconnected..."
                : "Ask JARVIS about your network, threats, infiltration..."
            }
            value={input}
            disabled={connectionStatus === "OFFLINE" || isProcessing}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Ask JARVIS about your network"
          />

          <div className="composer-actions">
            <button
              type="button"
              className={`mic-btn ${listening ? "listening" : ""}`}
              onClick={toggleListening}
              disabled={connectionStatus === "OFFLINE"}
              title={listening ? "Click to stop listening" : "Click to speak to JARVIS"}
              aria-label={listening ? "Stop voice listening" : "Start voice listening"}
              aria-pressed={listening}
            >
              🎙
            </button>

            <button
              type="button"
              className="send-btn"
              onClick={() => handleSubmitText()}
              disabled={!input.trim() || isProcessing || connectionStatus === "OFFLINE"}
              title="Send command"
              aria-label="Send command to JARVIS"
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
