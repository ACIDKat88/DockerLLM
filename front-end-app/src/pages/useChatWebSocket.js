// useChatWebSocket.js
import { useEffect, useRef } from 'react';

export function useChatWebSocket({ uid, personality, onMessage, onError, onClose }) {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!uid) return; // Ensure user id is provided

    // Use wss:// for secure connections if your backend is served over HTTPS
    const wsUrl = `wss://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat?uid=${uid}&personality=${personality}`;
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onopen = () => {
      console.log("WebSocket connection established");
    };

    socketRef.current.onmessage = (event) => {
      console.log("WebSocket message received:", event.data);
      onMessage && onMessage(event.data);
    };

    socketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      onError && onError(error);
    };

    socketRef.current.onclose = (event) => {
      console.log("WebSocket connection closed:", event);
      onClose && onClose(event);
    };

    // Clean up the WebSocket connection when component unmounts
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [uid, personality, onMessage, onError, onClose]);

  const sendMessage = (message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(message);
    } else {
      console.error("WebSocket is not open. Cannot send message:", message);
    }
  };

  return { sendMessage, socket: socketRef.current };
}
