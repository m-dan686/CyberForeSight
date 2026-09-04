import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import "./App.css";

const socket = io("http://localhost:5000");

export default function App() {
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [jarvis, setJarvis] = useState("Systems online. How can I help?");
  const [message, setMessage] = useState("");
  const [listening, setListening] = useState(false);

  const recognitionRef = useRef(null);

  useEffect(() => {
    socket.on("world_update", (world) => {
      setDevices(Object.values(world.devices || {}));
      setEvents((world.recentEvents || []).slice().reverse());
    });

    socket.on("device_update", (device) => {
      setDevices((prev) => [
        ...prev.filter((d) => d.hostname !== device.hostname),
        device,
      ]);
    });

    socket.on("jarvis_intelligence", (data) => {
      const response =
        data?.jarvis_report ||
        data?.report ||
        data?.response ||
        JSON.stringify(data);

      setJarvis(response);
      speak(response);
    });

    return () => {
      socket.off("world_update");
      socket.off("device_update");
      socket.off("jarvis_intelligence");
    };
  }, []);

  const speak = (text) => {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 0.95;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
  };

  const sendCommand = async (command) => {
    if (!command.trim()) return;

    setMessage("");

    try {
      const response = await fetch(
        "http://localhost:5000/voice-command",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ command }),
        }
      );

      const data = await response.json();

      const result =
        data?.result?.response ||
        data?.result?.jarvis_report ||
        data?.result?.report ||
        data?.response ||
        "I could not process that command.";

      setJarvis(result);
      speak(result);
    } catch {
      setJarvis("Unable to connect to JARVIS server.");
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setJarvis("Voice recognition is not supported.");
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = () => {
      setListening(true);
      setJarvis("I'm listening...");
    };

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setMessage(text);
      sendCommand(text);
    };

    recognition.onerror = () => {
      setListening(false);
      setJarvis("I couldn't hear that. Try again.");
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const getThreat = (device) => {
    const matching = events.filter(
      (e) =>
        e.device === device.hostname ||
        e.device === device.ip
    );

    if (!matching.length) return "normal";

    const risk = Math.max(
      ...matching.map((e) => Number(e.risk || 0))
    );

    if (risk >= 80) return "critical";
    if (risk >= 60) return "high";
    if (risk >= 30) return "medium";

    return "normal";
  };

  const radarPosition = (index, total) => {
    const angle = (index / Math.max(total, 1)) * Math.PI * 2;
    const radius = 37;

    return {
      left: `${50 + Math.cos(angle) * radius}%`,
      top: `${50 + Math.sin(angle) * radius}%`,
    };
  };

  return (
    <div className="jarvis">

      {/* HEADER */}

      <header className="header">
        <div className="logo-area">
          <div className="logo-orb">
            <span>J</span>
          </div>

          <div>
            <h1>JARVIS</h1>
            <p>ADAPTIVE CYBER INTELLIGENCE</p>
          </div>
        </div>

        <div className="online">
          <i></i>
          SYSTEM ONLINE
        </div>
      </header>


      {/* MAIN */}

      <main className="main-grid">

        {/* DEVICES */}

        <section className="glass devices">

          <div className="section-head">
            <span>CONNECTED DEVICES</span>
            <b>{devices.length}</b>
          </div>

          <div className="device-list">

            {devices.length === 0 && (
              <div className="no-devices">
                Waiting for devices...
              </div>
            )}

            {devices.map((device) => {
              const threat = getThreat(device);

              return (
                <div className="device" key={device.hostname}>

                  <div className="device-circle">
                    ●
                  </div>

                  <div className="device-data">
                    <strong>{device.hostname}</strong>
                    <small>{device.ip}</small>
                    <small>
                      CPU {device.cpu ?? "--"}%
                      &nbsp; RAM {device.ram ?? "--"}%
                    </small>
                  </div>

                  <span className={`threat ${threat}`}>
                    {threat}
                  </span>

                </div>
              );
            })}

          </div>
        </section>


        {/* RADAR */}

        <section className="glass radar-section">

          <div className="section-head">
            <span>NETWORK THREAT RADAR</span>

            <span className="live">
              ● LIVE
            </span>
          </div>

          <div className="radar">

            <div className="radar-grid"></div>

            <div className="ring r1"></div>
            <div className="ring r2"></div>
            <div className="ring r3"></div>

            <div className="cross x"></div>
            <div className="cross y"></div>

            <div className="sweep"></div>

            <div className="radar-core">
              <div className="core">
                J
              </div>

              <span>JARVIS</span>
            </div>

            {devices.map((device, index) => {
              const threat = getThreat(device);

              return (
                <div
                  key={device.hostname}
                  className={`radar-node ${threat}`}
                  style={radarPosition(
                    index,
                    devices.length
                  )}
                >
                  <div></div>
                  <span>{device.hostname}</span>
                </div>
              );
            })}

          </div>

          <div className="radar-info">
            <span>{devices.length} DEVICES</span>
            <span>{events.length} EVENTS</span>
            <span>REAL-TIME</span>
          </div>

        </section>


        {/* VOICE */}

        <section className="glass voice-section">

          <div className="voice-title">
            <span>JARVIS VOICE CONTROL</span>

            <small>
              {listening ? "LISTENING" : "READY"}
            </small>
          </div>

          <div className="voice-area">

            <div
              className={`voice-orb ${
                listening ? "active" : ""
              }`}
              onClick={startListening}
            >
              <div className="voice-inner">
                🎙
              </div>

              <div className="voice-ring ring-a"></div>
              <div className="voice-ring ring-b"></div>
              <div className="voice-ring ring-c"></div>
            </div>

            <h2>
              {listening
                ? "Listening..."
                : "Speak to JARVIS"}
            </h2>

            <p>
              {listening
                ? "Tell me what you need"
                : "Click the microphone to begin"}
            </p>

          </div>


          {/* SMALL CHAT */}

          <div className="chat">

            <input
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendCommand(message);
                }
              }}
              placeholder="Ask JARVIS..."
            />

            <button
              onClick={() => sendCommand(message)}
            >
              →
            </button>

          </div>

        </section>


        {/* RESPONSE */}

        <section className="glass response">

          <div className="section-head">
            <span>JARVIS RESPONSE</span>

            <span className="ai">
              AI ACTIVE
            </span>
          </div>

          <div className="response-text">
            {jarvis}
          </div>

        </section>

      </main>
    </div>
  );
}