import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from "react";
import Head from "next/head";
import styles from "../styles/Home.module.css";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import CircularProgress from "@mui/material/CircularProgress";
import Link from "next/link";
import { v4 as uuidv4 } from 'uuid';

declare global {
  interface Window {
    webkitSpeechRecognition: any;
  }
}

interface IMessage {
  role: string;
  content: string;
}

export default function Home() {
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<IMessage[]>([
    { role: "assistant", content: "Hi there! How can I help?" },
  ]);
  const [isListening, setIsListening] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  const messageListRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, []);

  useEffect(() => {
    // Generate a unique session ID
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
  }, []);

  const speak = (text: string): void => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = speechSynthesis.getVoices().find(voice => voice.lang === "en-US") || null;
      speechSynthesis.speak(utterance);
    }
  };

  const handleNewMessage = (newMessage: IMessage): void => {
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  };

  const handleError = (error: string): void => {
    handleNewMessage({
      role: "assistant",
      content: `Error: ${error}. Please try again.`,
    });
    setLoading(false);
    setUserInput("");
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement> | KeyboardEvent<HTMLTextAreaElement>): Promise<void> => {
    e.preventDefault();

    if (userInput.trim() === "" || loading) {
      return;
    }

    setLoading(true);
    await processVoiceMessage(userInput);
    setUserInput("");
  };

  const processVoiceMessage = async (message: string) => {
    if (message.trim() === "" || loading) {
      return;
    }
  
    setLoading(true);
    const newMessage = { role: "user", content: message };
    handleNewMessage(newMessage);
  
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages: [newMessage], session_id:sessionId }),
      });
  
      if (!response.ok) {
        throw new Error(response.statusText);
      }
  
      if (!response.body) {
        throw new Error("Response body is null");
      }
  
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedResponse = "";
  
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
  
        const chunkValue = decoder.decode(value);
	//console.log("-chunkValue-", chunkValue);
        accumulatedResponse += chunkValue;
        setCurrentResponse(accumulatedResponse);

	/*
        const lines = chunkValue.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.slice(5));
              if (jsonData.text) {
                accumulatedResponse += jsonData.text;
                setCurrentResponse(accumulatedResponse);
              }
            } catch (error) {
              if (line.trim() !== "[DONE]") {
                console.error("Parsing error:", error, "Line:", line);
              }
            }
          }
        }
	*/
      }
  
      handleNewMessage({
        role: "assistant",
        content: accumulatedResponse,
      });
  
      speak(accumulatedResponse); // Speak the entire response after it is accumulated
  
    } catch (error) {
      console.error("Error:", error);
      handleError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
      setCurrentResponse("");
    }
  };

  const handleEnter = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const startVoiceRecognition = (): void => {
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        await processVoiceMessage(transcript);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } else {
      alert('Speech recognition is not supported in your browser.');
    }
  };

  // ... (rest of the component remains the same)

  return (
    <>
      <Head>
        <title>Chat UI</title>
        <meta name="description" content="OpenAI interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className={styles.topnav}>
        <div className={styles.navlogo}>
          <Link href="/">Chat UI</Link>
        </div>
        <div className={styles.navlinks}>
          
            href="https://platform.openai.com/docs/models/gpt-4"
            target="_blank"
            rel="noopener noreferrer"
          <a>
            Docs
          </a>
        </div>
      </div>
      <main className={styles.main}>
        <div className={styles.cloud}>
          <div ref={messageListRef} className={styles.messagelist}>
            {messages.map((message, index) => (
              <div
                key={index}
                className={
                  message.role === "user"
                    ? styles.usermessage
                    : styles.apimessage
                }
              >
                {message.role === "assistant" ? (
                  <Image
                    src="/openai.png"
                    alt="AI"
                    width="30"
                    height="30"
                    className={styles.boticon}
                    priority={true}
                  />
                ) : (
                  <Image
                    src="/usericon.png"
                    alt="Me"
                    width="30"
                    height="30"
                    className={styles.usericon}
                    priority={true}
                  />
                )}
                <div className={styles.markdownanswer}>
                  <ReactMarkdown linkTarget={"_blank"}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
            {currentResponse && (
              <div className={styles.apimessage}>
                <Image
                  src="/openai.png"
                  alt="AI"
                  width="30"
                  height="30"
                  className={styles.boticon}
                  priority={true}
                />
                <div className={styles.markdownanswer}>
                  <ReactMarkdown linkTarget={"_blank"}>
                    {currentResponse}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className={styles.center}>
          <div className={styles.cloudform}>
            <form onSubmit={handleSubmit}>
              <textarea
                disabled={loading}
                onKeyDown={handleEnter}
                ref={textAreaRef}
                autoFocus={false}
                rows={1}
                maxLength={512}
                id="userInput"
                name="userInput"
                placeholder={
                  loading ? "Waiting for response..." : "Type your question..."
                }
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className={styles.textarea}
              />
              <button
                type="submit"
                disabled={loading}
                className={styles.generatebutton}
              >
                {loading ? (
                  <div className={styles.loadingwheel}>
                    <CircularProgress color="inherit" size={20} />
                  </div>
                ) : (
                  <svg
                    viewBox="0 0 20 20"
                    className={styles.svgicon}
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"></path>
                  </svg>
                )}
              </button>
              <button
                type="button"
                onClick={startVoiceRecognition}
                disabled={loading}
                className={styles.voicebutton}
              >
                {isListening ? (
                  <div className={styles.listeninganimation}></div>
                ) : (
                  <svg viewBox="0 0 24 24" className={styles.micicon}>
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                  </svg>
                )}
              </button>
            </form>
          </div>
          <div className={styles.footer}>
            <p>
              Powered by{" "}
              
                href="https://openai.com/"
                target="_blank"
                rel="noopener noreferrer"
              <a>
                OpenAI
              </a>
              .
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
