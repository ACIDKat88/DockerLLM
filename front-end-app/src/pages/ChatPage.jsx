import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import AppTheme from '../components/shared-theme/AppTheme.jsx';
import ColorModeSelect from '../components/shared-theme/ColorModeSelect.jsx';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import Toolbar from '@mui/material/Toolbar';
import { Box } from '@mui/material'; 
import ReactMarkdown from 'react-markdown';
import '../components/shared-theme/ChatPage.css';
import FeedbackButtons from '../components/shared-theme/feedbackbuttons';
import { getPersonas, logoutUser, getChatHistories, getUserPreferences, updateUserPreferences } from '../api'; // Import getPersonas, logoutUser, getChatHistories, and user preferences API functions
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import axios from 'axios';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import IconButton from '@mui/material/IconButton';

const availableModels = ["mistral:latest", "sskostyaev/mistral:7b-instruct-v0.2-q6_K-32k", "mistral:7b-instruct-v0.3-q3_K_M"];

// The readme markdown text
const readmeText = `
# **J1 Chatbot**

Choose your model and dataset.

Ask a question and I'll respond with an answer and sources.

**This bot does not have access to the internet thus does not have access to things like current dates etc.**

## **Uploaded Documents**

### **Airmen**
1. 55th Wing Incentive Awards Guide - March 2024
2. AFI 36-128: Pay Settings and Allowances - 7 April 21
3. AFMAN 36-2100: Military Utilization and Classification - 29 July 24
4. DAFI 36-2606: Reenlistment and Extension of Enlistment -  8 Aug 24
5. DAFI 36-3003 Military Leave Program - 9 Aug 24
6. DAFI 36-3211: Military Separation - 1 Aug 24
7. DAFMAN 36-203: Staffing Civilain Positions - 31 Oct 21
8. DAFMAN 36-2905: Department of the Air Force Physical Fitness Program -  21 Apr 22
9. DODII400.25V451_DAFI 3-1004: Department of the Air Force Civilian Recognition Programs
10. AFI 36-2406: Officer and Enlisted Evaluation Systems - 6 August 2024
11. AFI 36-2110: Total Force Assignments - 9 Aug 2024

### **USSTRATCOM**
1. CJCSI 1100.01E: Civilian Decorations and Awards - 17 Feb 2023
2. SI 230-01: Defense Military and Civilian Decorations Program - 1 May 24
3. SI 230-03: Personnel Recognition Programs
4. SI 230-04: Military and Civilian Retirement Certificates and Letters 19 July 23
`;


function ChatPage() {
  // Chat and UI state
  const [chatHistories, setChatHistories] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [showModels, setShowModels] = useState(false);
  const [dataset, setDataset] = useState("KG");
  const [temperature, setTemperature] = useState(1.0);
  const [persona, setPersona] = useState("None");
  const [selectedModel, setSelectedModel] = useState(availableModels[0]);
  const [sourceContent, setSourceContent] = useState(''); // state to hold sources markdown
  const navigate = useNavigate();
  const [availablePersonas, setAvailablePersonas] = useState(['None']); // Add state for personas
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem("session_token"));
  const [openReadme, setOpenReadme] = useState(false);
  const [lastInteractionData, setLastInteractionData] = useState(null);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [username, setUsername] = useState('User'); // Default username

  // Add state for tracking expanded sources
  const [expandedSources, setExpandedSources] = useState(false);
  const [expandedMessageSources, setExpandedMessageSources] = useState({});

  // Add state to track expanded state for individual sources
  const [expandedIndividualSources, setExpandedIndividualSources] = useState({});

  // Add state for tracking generation and abort controller
  const [isGenerating, setIsGenerating] = useState(false);
  const abortControllerRef = React.useRef(null);

  // Add state for tracking all unique sources and dropdown visibility
  const [allUniqueSources, setAllUniqueSources] = useState([]);
  const [showSourcesDropdown, setShowSourcesDropdown] = useState(false);
  // Add state for tracking sources by question
  const [sourcesByQuestion, setSourcesByQuestion] = useState({});
  // Add state for expanded questions
  const [expandedQuestions, setExpandedQuestions] = useState({});

  const sessionToken = localStorage.getItem("session_token");

  // Add this near the beginning with other state variables (around line ~50)
  const [sourcesCount, setSourcesCount] = useState(0);

  // Add a dedicated state variable for forcing UI refreshes
  // Add this with other state variables around line ~50
  const [forceUpdate, setForceUpdate] = useState(0);

  // Update the toggle sources function to automatically show the most recent question
  // Add a new ref to track the sources dropdown container
  const sourcesDropdownRef = React.useRef(null);

  // Add a ref for the messages container
  // Add this with other refs
  const messagesContainerRef = React.useRef(null);

  // Add new state variable near other state definitions (around line 70)
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info'); // 'success', 'info', 'warning', 'error'
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // Add new state variable near other state definitions (around line 72)
  const [displayablePersonas, setDisplayablePersonas] = useState(availablePersonas); // Start with all personas

  // Add this new state variable for hover effects
  const [hoveredButtonId, setHoveredButtonId] = useState(null);

  // Add state for hidden chat IDs
  const [hiddenChats, setHiddenChats] = useState([]);

  const handleLogout = async () => {
    try {
      await logoutUser(sessionToken);
    } catch (error) {
      console.error("Logout error:", error);
    }
    localStorage.removeItem("session_token");
    setIsLoggedIn(false);
    navigate("/signin");
  };

  // State for new chat dialog.
  const [newChatDialogOpen, setNewChatDialogOpen] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState('');

  // Assume uid is stored in localStorage.
  const uid = localStorage.getItem("user_id");

  async function fetchSources(query, dataset) {
    try {
      const response = await fetch("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/sources", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": sessionToken
        },
        body: JSON.stringify({ message: query, dataset })
      });
      if (response.ok) {
        const sourcesData = await response.json();
        let rawSourcesForFeedback = []; // Initialize default value
        
        // Assuming sourcesData itself might contain the array or pdf_elements is it
        if (sourcesData && Array.isArray(sourcesData.pdf_elements)) {
             rawSourcesForFeedback = sourcesData.pdf_elements;
        } else if (sourcesData && Array.isArray(sourcesData.sources)) {
            // Fallback if the key is named 'sources'
            rawSourcesForFeedback = sourcesData.sources;
        } else if (Array.isArray(sourcesData)) {
            // Fallback if the response *is* the array
            rawSourcesForFeedback = sourcesData;
        }

        // Process for display (URL modification)
        if (sourcesData.pdf_elements && sourcesData.pdf_elements.length > 0) {
          const prefix = "/home/cm36/Updated-LLM-Project/J1_corpus/cleaned/";
          sourcesData.pdf_elements = sourcesData.pdf_elements.map(el => {
            const absolute = el.pdf_url; // absolute path from metadata
            const relative = absolute.startsWith(prefix) ? absolute.substring(prefix.length) : absolute;
            // Remove duplicate extension if present.
            const fixedRelative = relative.endsWith(".pdf.pdf") ? relative.slice(0, -4) : relative;
            // Build the URL using the static mount:
            el.pdf_url = `/static/${encodeURIComponent(fixedRelative)}`;
            return el;
          });
        }
        
        // Update state with the markdown content for display
        setSourceContent(sourcesData.content || '');
        
        console.log("Source content received:", sourcesData.content);
        
        // Extract sources from the markdown to add to our unique sources list
        const parsedSources = parseSourcesMarkdown(sourcesData.content || '');
        console.log("Parsed sources:", parsedSources);
        
        if (parsedSources.length > 0) {
          // Get the current question number
          // Count the user messages up to this point
          const questionNumber = messages.filter(msg => msg.sender === 'user').length;
          
          // Update allUniqueSources with only unique entries
          setAllUniqueSources(prevSources => {
            // Create a new Set with all current sources
            const currentSourceTitles = new Set(prevSources.map(source => source.title));
            
            // Filter out sources we already have
            const newSources = parsedSources.filter(source => !currentSourceTitles.has(source.title));
            console.log("New unique sources:", newSources);
            
            // Return updated array with new unique sources added
            const updatedSources = [...prevSources, ...newSources];
            console.log("All unique sources after update:", updatedSources);
            return updatedSources;
          });
          
          // Update sourcesByQuestion with the new sources for this question
          setSourcesByQuestion(prev => {
            const updated = { ...prev };
            if (!updated[questionNumber]) {
              updated[questionNumber] = [];
            }
            
            // Add the new sources to this question, avoid duplicates
            const currentTitles = new Set(updated[questionNumber].map(s => s.title));
            parsedSources.forEach(source => {
              if (!currentTitles.has(source.title)) {
                updated[questionNumber].push(source);
              }
            });
            
            return updated;
          });

          // CRITICAL: Force UI update for source count and dropdown
          setTimeout(() => {
            console.log("FORCING UPDATE: Recalculating sources after fetch");
            // Force update the sources count
            const total = calculateTotalSources();
            setSourcesCount(total);
            
            // Force a UI refresh
            setForceUpdate(prev => prev + 1);
            
            // Also force the sources dropdown to update if it's open
            if (showSourcesDropdown) {
              setShowSourcesDropdown(false);
              setTimeout(() => setShowSourcesDropdown(true), 50);
            }
          }, 200);
        } else {
          console.log("No sources parsed from the content");
        }

        // Return the raw source data needed for feedback
        return rawSourcesForFeedback; 
      } else {
        console.error("Error fetching sources:", await response.text());
        return []; // Return empty array on error
      }
    } catch (error) {
      console.error("Error fetching sources:", error);
      return []; // Return empty array on error
    }
  }
  
  
  
  // Modify the chat history useEffect to remove polling
  useEffect(() => {
    // Only fetch chat histories once on initial load
    fetchChatHistories();
    
    // No polling interval setup or cleanup needed
  }, [sessionToken]);

  // Create a separate fetchChatHistories function outside the useEffect
  const fetchChatHistories = async () => {
    try {
      const response = await fetch(
        'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat/histories',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': sessionToken
          }
        }
      );
      if (!response.ok) {
        setChatHistories([]);
        return;
      }
      const data = await response.json();
      
      // Convert chat sessions (object) into an array.
      const histories = Object.entries(data).map(([chatId, chatObj]) => ({
        id: chatId,
        title: chatObj.title,
        // Don't load messages here to prevent re-renders
        hasMessages: Array.isArray(chatObj.messages) && chatObj.messages.length > 0
      }));
      
      // Sort histories by timestamp (extracted from chatId) in descending order.
      const sortedHistories = histories.sort((a, b) => {
        const aTimestamp = a.id.substring(a.id.indexOf('-') + 1);
        const bTimestamp = b.id.substring(b.id.indexOf('-') + 1);
        return bTimestamp.localeCompare(aTimestamp);
      });
      
      // Keep only the 10 most recent chats.
      // Only update the list of available chats, not their content
      setChatHistories(prevHistories => {
        // If no previous histories, use the new ones
        if (prevHistories.length === 0) {
          return sortedHistories.slice(0, 10);
        }
        
        // Otherwise, maintain content of currently selected chat
        return sortedHistories.slice(0, 10).map(newChat => {
          // If this is the currently selected chat, preserve its messages
          if (newChat.id === selectedChat) {
            const currentChat = prevHistories.find(ch => ch.id === selectedChat);
            return {
              ...newChat,
              messages: currentChat?.messages || []
            };
          }
          return newChat;
        });
      });
      
      // Only set messages if no chat is selected yet (first time load)
      if (sortedHistories.length > 0 && !selectedChat) {
        // For first load, we need to fetch the messages for the selected chat
        await loadChatMessages(sortedHistories[0].id);
      }
    } catch (error) {
      console.error("Error fetching chat histories:", error);
      setChatHistories([]);
    }
  };

  // Add a scroll to bottom function
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      const { scrollHeight, clientHeight } = messagesContainerRef.current;
      messagesContainerRef.current.scrollTop = scrollHeight - clientHeight;
    }
  };

  // Add useEffect to scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Modify the loadChatMessages function to ensure consistent message formatting
  const loadChatMessages = async (chatId) => {
    try {
      // Get all chat histories and find the specific one we want
      const response = await fetch(
        'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat/histories',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': sessionToken
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        
        // Find the specific chat by ID
        const chatData = Object.entries(data).find(([id, _]) => id === chatId);
        
        if (chatData && chatData.length > 1) {
          const [id, chatInfo] = chatData;
          
          // Process messages to identify which ones have sources
          let processedMessages = [];
          let initialSourceStates = {};
          
          if (Array.isArray(chatInfo.messages)) {
            // First, check if any messages already have source information
            processedMessages = chatInfo.messages.map((msg, index) => {
              // Ensure message has all required properties for styling
              const normalizedMsg = {
                ...msg,
                // Ensure sender is either 'user', 'bot', or 'sources'
                sender: msg.sender || (msg.role === 'user' ? 'user' : 'bot'),
                // Ensure content exists
                content: msg.content || msg.text || "",
              };
              
              // If this is a bot message and the next message is a sources message,
              // mark it as having sources
              const hasFollowingSources = index < chatInfo.messages.length - 1 && 
                                         chatInfo.messages[index + 1]?.sender === 'sources';
              
              if (normalizedMsg.sender === 'bot') {
                // Check if the message already has hasSources flag
                if (normalizedMsg.hasSources !== undefined) {
                  // Initialize expansion state for this message
                  initialSourceStates[index] = false;
                  return normalizedMsg; // Keep existing flags
                }
                
                // Otherwise, look for adjacent sources
                if (hasFollowingSources) {
                  // Initialize expansion state for this message
                  initialSourceStates[index] = false;
                  return {
                    ...normalizedMsg,
                    hasSources: true,
                    sourcesMarkdown: chatInfo.messages[index + 1].content
                  };
                }
              }
              
              // For non-bot messages or those without sources, return normalized message
              return normalizedMsg;
            });
            
            // Filter out standalone sources messages that we've now incorporated into bot messages
            processedMessages = processedMessages.filter((msg, index) => {
              // Keep if not a sources message or if it's not immediately after a bot message
              return msg.sender !== 'sources' || 
                    index === 0 || 
                    processedMessages[index - 1]?.sender !== 'bot';
            });
          }
          
          // Update the selected chat and its messages
          setSelectedChat(chatId);
          setMessages(processedMessages);
          
          // Reset sources when changing chats
          setLastInteractionData(null);
          setSourceContent('');
          // Initialize expansion states for all messages with sources
          setExpandedMessageSources(initialSourceStates);
          
          // Also update the chat histories with the loaded messages
          setChatHistories(prev => {
            const updated = [...prev];
            const chatIndex = updated.findIndex(chat => chat.id === chatId);
            if (chatIndex !== -1) {
              updated[chatIndex] = {
                ...updated[chatIndex],
                messages: processedMessages
              };
            }
            return updated;
          });
          
          // Scroll to bottom after messages are loaded
          setTimeout(scrollToBottom, 100);
        } else {
          console.error("Chat not found:", chatId);
        }
      } else {
        console.error("Error fetching chat histories:", await response.text());
      }
    } catch (error) {
      console.error("Error loading chat messages:", error);
    }
  };

  // Modify the handler for selecting a chat
  const handleSelectChat = (chatId) => {
    if (chatId !== selectedChat) {
      // Reset all sources-related state when switching chats
      setAllUniqueSources([]);
      setSourcesByQuestion({});
      setExpandedIndividualSources({});
      setExpandedMessageSources({});
      setExpandedQuestions({});
      setSourcesCount(0);
      setSourceContent('');
      setShowSourcesDropdown(false);
      
      // Load the selected chat messages
      loadChatMessages(chatId);
    }
  };

  // New chat dialog functions.
  const handleNewChat = () => {
    setNewChatTitle('');
    setNewChatDialogOpen(true);
  };

  const handleCreateChat = async () => {
    try {
      const response = await fetch(
        'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat/histories',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': sessionToken
          },
          body: JSON.stringify({ chat_title: newChatTitle })
        }
      );
      if (response.ok) {
        const newChatSession = await response.json();
        
        // After creating a new chat, refresh the chat histories
        await fetchChatHistories();
        
        // Reset all sources-related state for the new chat
        setAllUniqueSources([]);
        setSourcesByQuestion({});
        setExpandedIndividualSources({});
        setExpandedMessageSources({});
        setExpandedQuestions({});
        setSourcesCount(0);
        setSourceContent('');
        setShowSourcesDropdown(false);
        
        // Then select the new chat
        await loadChatMessages(newChatSession.id);
        
        setNewChatDialogOpen(false);
      } else {
        console.error("Error creating chat session:", await response.text());
      }
    } catch (error) {
      console.error("Error creating chat session:", error);
    }
  };

  // Handle sending messages.
  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    // Check for inappropriate content before sending
    const sanitizationResult = sanitizeUserInput(userInput);
    if (!sanitizationResult.isAppropriate) {
      // Display warning and don't send the message
      setMessages(prev => [...prev, { 
        sender: 'bot', 
        content: "I'm sorry, but your message appears to contain inappropriate content that I cannot respond to. Please revise your question."
      }]);
      return;
    }

    // Save the current query before clearing userInput.
    const currentUserQuery = userInput;

    // Append the user's message.
    setMessages(prev => [...prev, { sender: 'user', content: currentUserQuery }]);
    setUserInput(''); // Clear input immediately after appending user message
    setLastInteractionData(null); // Clear previous interaction data
    setSourceContent(''); // Clear previous sources display
    
    // Set generating state to true and create new abort controller
    setIsGenerating(true);
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    console.log("[handleSendMessage] Current persona state:", persona); // Log persona state
    const payload = {
      message: currentUserQuery,
      model: selectedModel,
      temperature: temperature,
      dataset: dataset,
      persona: persona, 
      chat_id: selectedChat
    };

    // Add clear logging of which dataset is being used
    console.log(`[DEBUG] Sending message with dataset: "${dataset}" to connect to table: document_embeddings_${dataset === "KG" ? "combined" : dataset.toLowerCase()}`);

    const startTime = performance.now(); // Record start time
    let botMessage = ""; // Accumulate raw bot response
    let cleanedBotMessage = ""; // Accumulate cleaned bot response
    let messageIndex = null; // Track the index of the bot message for source association

    try {
      const response = await fetch(
        'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': sessionToken,
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
          },
          body: JSON.stringify(payload),
          signal // Add the abort signal to the fetch request
        }
      );

      if (!response.body) {
        throw new Error("ReadableStream not supported in this browser.");
      }

      console.log("[DEBUG] Starting to read stream...");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Add an empty bot message placeholder to update later.
      setMessages(prev => {
        messageIndex = prev.length; // Store the index of this message
        return [...prev, { sender: 'bot', content: "" }];
      });

      let streamDone = false;
      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;
        const buffer = decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") {
              streamDone = true;
              break;
            }
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.token) {
                let token = parsed.token;
                // Accumulate raw token first
                botMessage += token; 
                
                // Simplified cleaning logic (apply more robust cleaning if needed)
                let cleanedToken = token;
                if (token.includes("content=")) { 
                  const parts = token.split("content=");
                  cleanedToken = ""; // Reset for this potentially multi-part token
                  for (const part of parts) {
                    if (part.startsWith("'") || part.startsWith('"')) {
                      const quoteChar = part[0];
                      const endQuoteIndex = part.indexOf(quoteChar, 1);
                      if (endQuoteIndex !== -1) {
                        cleanedToken += part.substring(1, endQuoteIndex);
                      }
                    } else {
                      // Append parts that don't look like content strings (might be metadata)
                      // This part might need refinement based on actual stream format
                    }
                  }
                }
                
                // Append the cleaned part to the display message
                cleanedBotMessage += cleanedToken; 
                
                // Normalize line breaks in the message to maintain structure
                const displayMessage = cleanedBotMessage
                  .replace(/\\n/g, "\n")           // Convert literal '\n' to newlines
                  .replace(/\\\\n/g, "\n")         // Handle double-escaped newlines
                  .replace(/\r\n?/g, "\n")         // Normalize CRLF to LF
                  .replace(/\n{3,}/g, "\n\n")      // Limit to max 2 consecutive line breaks
                  .replace(/ {2,}/g, " ")          // Remove extra spaces
                  .replace(/\\$/gm, "")            // Remove trailing backslashes at end of lines
                  .replace(/\\(?!\S)/g, "");       // Remove standalone backslashes

                setMessages(prev => {
                  const updated = [...prev];
                  if (updated.length > 0 && updated[updated.length - 1].sender === 'bot') {
                      updated[updated.length - 1].content = displayMessage;
                  }
                  return updated;
                });
              }
            } catch (err) {
              console.error("Error parsing token JSON:", err, dataStr);
            }
          }
        }
      }
      console.log("[DEBUG] Final bot message (cleaned):", cleanedBotMessage);
      
      const endTime = performance.now(); // Record end time
      const elapsedTime = (endTime - startTime) / 1000; // Elapsed time in seconds

      // --- Fetch sources AFTER stream is done --- 
      let fetchedSources = []; // Default to empty array
      let sourcesMarkdown = '';
      if (dataset !== "None") { // Only fetch sources if dataset is not None
        fetchedSources = await fetchSources(currentUserQuery, dataset);
        sourcesMarkdown = sourceContent; // Capture the current sources markdown
        console.log("Sources markdown captured:", sourcesMarkdown);
        
        // CRITICAL FIX: Directly update the message with sources, don't rely on later updates
        if (messageIndex !== null && sourcesMarkdown) {
          // Parse sources from the markdown for immediate use
          const parsedSources = parseSourcesMarkdown(sourcesMarkdown);
          console.log("Parsed sources for immediate attachment:", parsedSources);
          
          // Force flag to always show sources if we have them
          const hasSources = parsedSources.length > 0;
          console.log("Setting hasSources =", hasSources, "for message", messageIndex);
          
          setMessages(prev => {
            const updated = [...prev];
            if (updated[messageIndex]) {
              updated[messageIndex] = {
                ...updated[messageIndex],
                hasSources: hasSources,
                sourcesMarkdown: sourcesMarkdown,
                sources: parsedSources // Add the parsed sources directly
              };
            }
            return updated;
          });
          
          // Immediately make sources expandable if we have any
          if (hasSources) {
            setExpandedMessageSources(prev => ({
              ...prev,
              [messageIndex]: false // Default to collapsed for new messages with sources
            }));
          }
          
          // Update sourcesByQuestion immediately
          const questionNumber = messageIndex > 0 ? 
            prev => prev.filter(msg => msg.sender === 'user').length : 
            1; // Fallback to 1 if we can't count
          
          setSourcesByQuestion(prev => {
            const updated = { ...prev };
            if (!updated[questionNumber]) {
              updated[questionNumber] = [];
            }
            
            // Add sources, avoiding duplicates
            const currentTitles = new Set(updated[questionNumber].map(s => s.title));
            parsedSources.forEach(source => {
              if (!currentTitles.has(source.title)) {
                updated[questionNumber].push(source);
              }
            });
            
            return updated;
          });
          
          // Also update allUniqueSources
          setAllUniqueSources(prevSources => {
            // Create a new Set with all current sources
            const currentSourceTitles = new Set(prevSources.map(source => source.title));
            
            // Filter out sources we already have
            const newSources = parsedSources.filter(source => !currentSourceTitles.has(source.title));
            
            // Return updated array with new unique sources added
            const updatedSources = [...prevSources, ...newSources];
            console.log("All unique sources after update:", updatedSources);
            return updatedSources;
          });
          
          // EXPLICITLY force the sources button to update by recalculating total
          // This is key to fixing the bug where the count doesn't update
          setTimeout(() => {
            const updatedTotal = calculateTotalSources();
            console.log("SOURCES COUNT UPDATE: Button should now show", updatedTotal, "sources");
            
            // Force a UI refresh to ensure the sources button updates
            setOpenSnackbar(prevState => {
              setTimeout(() => setOpenSnackbar(false), 100);
              return true;
            });
          }, 200);
        }
      } else {
        setSourceContent(''); // Ensure sources are cleared if dataset is None
      }

      // --- Assemble interaction data for feedback --- 
      const interactionData = {
          question: currentUserQuery,
          answer: cleanedBotMessage,
          sources: fetchedSources,
          sourcesMarkdown: sourcesMarkdown,
          model: selectedModel,
          temperature: temperature,
          dataset: dataset,
          personality: persona,
          chat_id: selectedChat,
          elapsed_time: elapsedTime,
          messageIndex: messageIndex
      };
      // Force ensure lastInteractionData is set (change setLastInteractionData to this):
      console.log("Setting lastInteractionData for feedback buttons");
      setLastInteractionData(interactionData);

      // FORCE REFRESH: Reload the current chat to ensure everything is displayed properly
      console.log("Forcing refresh of chat data...");
      if (selectedChat) {
        // We need to reload the full chat with fresh data
        await loadChatMessages(selectedChat);
        
        // Force refresh of the All Sources dropdown using the latest message with sources
        const latestBot = messages.filter(msg => msg.sender === 'bot').pop();
        if (latestBot && (latestBot.sources || latestBot.sourcesMarkdown)) {
          const parsedSources = latestBot.sources || 
                                (latestBot.sourcesMarkdown ? 
                                parseSourcesMarkdown(latestBot.sourcesMarkdown) : 
                                []);
          
          if (parsedSources.length > 0) {
            // Update sourcesByQuestion with the latest sources
            const questionNumber = messages.filter(msg => msg.sender === 'user').length;
            setSourcesByQuestion(prev => {
              const updated = { ...prev };
              if (!updated[questionNumber]) {
                updated[questionNumber] = [];
              }
              
              // Add the new sources, avoiding duplicates
              const currentTitles = new Set(updated[questionNumber].map(s => s.title));
              parsedSources.forEach(source => {
                if (!currentTitles.has(source.title)) {
                  updated[questionNumber].push(source);
                }
              });
              
              return updated;
            });
            
            // Update allUniqueSources for completeness
            setAllUniqueSources(prevSources => {
              const currentSourceTitles = new Set(prevSources.map(source => source.title));
              const newSources = parsedSources.filter(source => !currentSourceTitles.has(source.title));
              return [...prevSources, ...newSources];
            });
          }
        }
        
        // Also force refresh of the sources count
        const newTotalSources = calculateTotalSources();
        console.log("Updated sources count:", newTotalSources);
      }

    } catch (error) {
      // Check if this is an abort error
      if (error.name === 'AbortError') {
        console.log('LLM generation was aborted');
        
        // Remove the bot's message entirely when generation is stopped
        setMessages(prev => {
          // Remove the last message if it's from the bot
          if (prev.length > 0 && prev[prev.length - 1].sender === 'bot') {
            return prev.slice(0, -1);
          }
          return prev;
        });
        
        // Clear any cached data to ensure nothing is saved
        messageIndex = null;
      } else {
        console.error("Error sending message:", error);
        setMessages(prev => {
          const updated = [...prev];
          if (updated.length > 0 && updated[updated.length - 1].sender === 'bot') {
            updated[updated.length - 1].content = "Error processing request.";
          }
          return updated;
        });
      }
      setLastInteractionData(null); // Clear data on error
    } finally {
      // Always set generating to false when done
      setIsGenerating(false);
      abortControllerRef.current = null;
      
      // Scroll to bottom
      setTimeout(scrollToBottom, 100);
      
      // AGGRESSIVE APPROACH: Force refresh everything with a short delay
      setTimeout(() => {
        console.log("FORCE REFRESH: Updating sources after small delay");
        
        // Force recalculation of total sources directly
        const userMsgs = messages.filter(msg => msg.sender === 'user').length;
        console.log(`Total user messages: ${userMsgs}`);
        
        // Force update of sources by question
        const sourcesFromMessages = [];
        const tempSourcesByQuestion = {...sourcesByQuestion};
        
        // Scan through all messages to collect sources
        messages.forEach((msg, idx) => {
          if (msg.sender === 'bot' && (msg.hasSources || msg.sourcesMarkdown || (msg.sources && msg.sources.length > 0))) {
            // Find the corresponding user message index
            const prevUserMsgs = messages.slice(0, idx).filter(m => m.sender === 'user').length;
            const questionNum = prevUserMsgs;
            
            const sources = msg.sources || 
                           (msg.sourcesMarkdown ? parseSourcesMarkdown(msg.sourcesMarkdown) : []);
            
            if (sources.length > 0) {
              // Ensure this question has an entry
              if (!tempSourcesByQuestion[questionNum]) {
                tempSourcesByQuestion[questionNum] = [];
              }
              
              // Add each source, avoiding duplicates
              sources.forEach(source => {
                const existingSource = tempSourcesByQuestion[questionNum].find(s => s.title === source.title);
                if (!existingSource) {
                  tempSourcesByQuestion[questionNum].push(source);
                  allMessageSources.push(source);
                }
              });
            }
          }
        });
        
        // Force refresh of sourcesByQuestion and allUniqueSources
        setSourcesByQuestion({...tempSourcesByQuestion});
        
        // Combine all sources into allUniqueSources
        const uniqueTitles = new Set();
        const uniqueSources = [];
        sourcesFromMessages.forEach(source => {
          if (!uniqueTitles.has(source.title)) {
            uniqueTitles.add(source.title);
            uniqueSources.push(source);
          }
        });
        
        if (uniqueSources.length > 0) {
          setAllUniqueSources(uniqueSources);
        }
        
        // Force update the sources count
        const total = calculateTotalSources();
        setSourcesCount(total);
        
        // Force the sources dropdown to update if it's open
        if (showSourcesDropdown) {
          setShowSourcesDropdown(false);
          setTimeout(() => setShowSourcesDropdown(true), 50);
        }
        
        // Force a UI refresh by updating the forceUpdate state
        setForceUpdate(prev => prev + 1);
        
        // Force re-render by updating a dummy state if needed
        setOpenSnackbar(prev => {
          setTimeout(() => setOpenSnackbar(false), 100);
          return true;
        });
      }, 500);
      
      // Also ensure feedback buttons are enabled by restoring lastInteractionData if needed
      if (!lastInteractionData) {
        const lastBotMsg = messages.filter(msg => msg.sender === 'bot').pop();
        const lastUserMsg = messages.filter(msg => msg.sender === 'user').pop();
        
        if (lastBotMsg && lastUserMsg) {
          const forcedInteractionData = {
            question: lastUserMsg.content,
            answer: lastBotMsg.content,
            sources: lastBotMsg.sources || [],
            sourcesMarkdown: lastBotMsg.sourcesMarkdown || '',
            model: selectedModel,
            temperature: temperature,
            dataset: dataset,
            personality: persona,
            chat_id: selectedChat,
            elapsed_time: 0, // Default since we don't have the real value
            messageIndex: messages.indexOf(lastBotMsg)
          };
          
          console.log("FORCE ENABLING FEEDBACK BUTTONS");
          setLastInteractionData(forcedInteractionData);
        }
      }
    }
  };

  // Function to sanitize user input and check for inappropriate content
  const sanitizeUserInput = (input) => {
    // Convert to lowercase for easier matching
    const lowerCaseInput = input.toLowerCase();
    
    // Define patterns for inappropriate content
    const inappropriatePatterns = [
      // Profanity and offensive language
      /\b(f[u\*]+ck|sh[i\*]+t|b[i\*]+tch|c[u\*]+nt|a[s\*]+hole|d[i\*]+ck|p[u\*]+ssy|porn|xxx)\b/,
      
      // Harmful instructions
      /\b(how to (make|create|build) (bomb|explosive|weapon|virus|malware))\b/,
      
      // Requests for illegal content
      /\b(illegal (drugs|content)|child (porn|abuse)|underage)\b/,
      
      // Hate speech indicators
      /\b(kill|murder|attack|bomb|shoot|harm|hurt) (people|group|community|race|religion)\b/,
      
      // Add more patterns as needed
    ];
    
    // Check if any inappropriate pattern matches
    for (const pattern of inappropriatePatterns) {
      if (pattern.test(lowerCaseInput)) {
        console.log("Inappropriate content detected:", pattern);
        return {
          isAppropriate: false,
          reason: "Contains inappropriate or harmful content"
        };
      }
    }
    
    // If no inappropriate patterns matched, the input is considered appropriate
    return {
      isAppropriate: true,
      sanitizedInput: input.trim()
    };
  };

  // *** ADDED: Function to handle Enter key press ***
  const handleKeyDown = (event) => {
    // Check if Enter key is pressed without the Shift key
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Prevent default behavior (newline)
      handleSendMessage();    // Call the send message function
    }
  };

  // Function to format model name for display
  const formatModelName = (modelName) => {
    if (modelName === "mistral:7b-instruct-v0.3-q3_K_M") {
      return "Mistral:7BQ";
    } else if (modelName === "sskostyaev/mistral:7b-instruct-v0.2-q6_K-32k") {
      return "mistral:small";
    }
    return modelName; // Return the original name if no specific format is defined
  };

  const handleSelectModel = (model) => {
    setSelectedModel(model);
    setShowModels(false);
    
    // Automatically save the model preference to the server
    if (sessionToken) {
      const backendPreferences = {
        selected_model: model,
        temperature: temperature,
        dataset: dataset,
        persona: persona
      };
      
      const endpoint = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences";
      
      fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": sessionToken,
        },
        body: JSON.stringify(backendPreferences),
      })
      .then(response => {
        if (response.ok) {
          console.log("[SUCCESS] Model preference automatically saved");
          return response.json();
        } else {
          console.log("[ERROR] Failed to auto-save model preference");
          throw new Error("Failed to save model preference");
        }
      })
      .then(data => {
        console.log("[DEBUG] Server response for auto-save:", data);
      })
      .catch(error => {
        console.error("Error auto-saving model preference:", error);
      });
    }
  };

  useEffect(() => {
    setIsLoggedIn(!!sessionToken);
  }, [sessionToken]);

  // Fetch available personas on component mount
  useEffect(() => {
    async function fetchPersonas() {
      try {
        const personas = await getPersonas();
        if (Array.isArray(personas)) {
          if (!personas.includes('None')) {
            personas.unshift('None'); 
          }
          setAvailablePersonas(personas); // Store the full list
          setDisplayablePersonas(personas); // Initialize displayable list
        } else {
           console.error("Fetched personas is not an array:", personas);
           setAvailablePersonas(['None']); 
           setDisplayablePersonas(['None']);
        }
      } catch (error) {
        console.error("Error fetching available personas:", error);
        setAvailablePersonas(['None']); 
        setDisplayablePersonas(['None']);
      }
    }
    fetchPersonas();
  }, []); // Runs once on mount

  // Function to fetch user preferences
  useEffect(() => {
    async function fetchUserPreferences() {
      if (!sessionToken) return;
      
      // Fetch from the API directly, similar to feedback buttons approach
      const endpoint = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences";
      
      try {
        const response = await fetch(endpoint, {
          method: 'GET',
          headers: {
            "Content-Type": "application/json",
            "Authorization": sessionToken,
          }
        });
        
        console.log(`[DEBUG] User preferences response status: ${response.status}`);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`[DEBUG] Loaded server preferences:`, data);
          
          // Apply preferences to state
          if (data.selected_model && availableModels.includes(data.selected_model)) {
            setSelectedModel(data.selected_model);
          }
          if (data.dataset) {
            setDataset(data.dataset);
          }
          if (data.temperature !== undefined) {
            setTemperature(data.temperature);
          }
          if (data.persona) {
            setPersona(data.persona);
          }
          
          console.log("[SUCCESS] Preferences loaded from server");
        } else {
          console.log(`[DEBUG] Server preferences not available: ${response.status}`);
          console.log("[INFO] Using default preferences");
        }
      } catch (error) {
        console.error("Error fetching user preferences:", error);
        console.log("[INFO] Using default preferences");
      }
      
      // Mark preferences as loaded regardless of success/failure
      setPreferencesLoaded(true);
    }
    
    fetchUserPreferences();
  }, [sessionToken]);

  // Add a function to handle saving preferences when Confirm button is clicked
  const handleSavePreferences = async () => {
    if (!sessionToken) return;
    
    console.log("[DEBUG] Saving preferences:", { model: selectedModel, dataset, temperature, persona });
    
    const backendPreferences = {
      selected_model: selectedModel,
      temperature: temperature,
      dataset: dataset,
      persona: persona
    };
    
    const endpoint = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences";
    
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": sessionToken,
        },
        body: JSON.stringify(backendPreferences),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log(`[DEBUG] Error saving preferences: ${errorText}`);
        setSnackbarMessage(`Error saving settings: ${errorText}`);
        setSnackbarSeverity('error');
      } else {
        const data = await response.json();
        console.log("[SUCCESS] User preferences saved to server", data);
        
        // Update UI state based on saved preferences returned from backend
        if (data.selected_model && availableModels.includes(data.selected_model)) {
          setSelectedModel(data.selected_model);
        }
        if (data.dataset) {
          setDataset(data.dataset);
        }
        if (data.temperature !== undefined) {
          setTemperature(data.temperature);
        }
        if (data.persona) {
          setPersona(data.persona);
        }
        // Set specific message and severity for confirmation
        setSnackbarMessage("Settings Confirmed");
        setSnackbarSeverity('success'); // Use success severity
      }

      setOpenSnackbar(true); // Show snackbar for success or error
    } catch (error) {
      console.error("Error saving user preferences:", error);
      setSnackbarMessage("Failed to save settings due to network or server error.");
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    }
    
    setShowSettings(false);
  };

  // Handle closing the snackbar
  const handleCloseSnackbar = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    // Close both snackbars to ensure all notifications can be dismissed
    setSnackbarOpen(false);
    setOpenSnackbar(false);
  };

  // Fetch username when component mounts
  useEffect(() => {
    console.log("Attempting to fetch username with token:", !!sessionToken);
    
    // First, check if username is already in localStorage
    const storedUsername = localStorage.getItem("username");
    if (storedUsername) {
      console.log("Using username from localStorage:", storedUsername);
      setUsername(storedUsername);
      return; // Stop further processing if we already have the username
    }
    
    if (sessionToken) {
      // Using axios like in the adminpage.jsx example
      const headers = { 
        "Content-Type": "application/json",
        "Authorization": sessionToken 
      };
      
      console.log("Making API call to fetch username...");
      
      // Try multiple endpoints to find the one that works
      // First try /api/me endpoint
      axios.get("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/me", { headers })
        .then(response => {
          console.log("Username API response from /api/me:", response.data);
          
          if (response.data && response.data.username) {
            console.log("Setting username from /api/me:", response.data.username);
            setUsername(response.data.username);
            localStorage.setItem("username", response.data.username);
            return null; // Signal that we don't need to try other endpoints
          } else if (response.data && response.data.user && response.data.user.username) {
            console.log("Setting username from /api/me user object:", response.data.user.username);
            setUsername(response.data.user.username);
            localStorage.setItem("username", response.data.user.username);
            return null; // Signal that we don't need to try other endpoints
          } else {
            // If the first endpoint didn't work, try another endpoint
            console.log("Username not found in /api/me response, trying /api/user");
            return axios.get("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/user", { headers });
          }
        })
        .then(response => {
          if (!response) return null; // If we already handled the username above
          
          console.log("Username API response from /api/user:", response.data);
          
          if (response.data && response.data.username) {
            console.log("Setting username from /api/user:", response.data.username);
            setUsername(response.data.username);
            localStorage.setItem("username", response.data.username);
            return null;
          } else if (response.data && response.data.user && response.data.user.username) {
            console.log("Setting username from /api/user user object:", response.data.user.username);
            setUsername(response.data.user.username);
            localStorage.setItem("username", response.data.user.username);
            return null;
          } else {
            console.log("Username not found in /api/user response, trying /api/current_user");
            return axios.get("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/current_user", { headers });
          }
        })
        .then(response => {
          if (!response) return;
          
          console.log("Username API response from /api/current_user:", response.data);
          
          if (response.data && response.data.username) {
            console.log("Setting username from /api/current_user:", response.data.username);
            setUsername(response.data.username);
            localStorage.setItem("username", response.data.username);
          }
        })
        .catch(error => {
          console.error("Error fetching username:", error);
          
          // Let's also try to extract username from session token as last resort
          try {
            // If token is in JWT format, try to decode it
            const tokenParts = sessionToken.split('.');
            if (tokenParts.length === 3) {
              const payload = JSON.parse(atob(tokenParts[1]));
              console.log("JWT token payload:", payload);
              if (payload.username || payload.sub || payload.name) {
                const extractedName = payload.username || payload.sub || payload.name;
                console.log("Setting username from JWT token:", extractedName);
                setUsername(extractedName);
                localStorage.setItem("username", extractedName);
                return;
              }
            }
          } catch (e) {
            console.log("Token is not in JWT format or cannot be decoded");
          }
          
          // Final fallback to user_id if all else fails
          const userId = localStorage.getItem("user_id");
          if (userId) {
            console.log("Using user_id as final fallback:", userId);
            setUsername(userId);
          }
        });
    } else {
      // No session token, use user_id as fallback
      const userId = localStorage.getItem("user_id");
      if (userId) {
        console.log("No session token, using user_id:", userId);
        setUsername(userId);
      }
    }
  }, [sessionToken]);

  // Function to extract direct source data from a bot message
  const getSourcesFromMessage = (message) => {
    // Log the entire message object to debug
    console.log("getSourcesFromMessage - Full message:", JSON.stringify(message, null, 2));
    
    // First check if message has direct sources attached
    if (message.sources && Array.isArray(message.sources)) {
      console.log("Using direct sources from message:", message.sources);
      return message.sources;
    }
    
    // If we have hasSources flag but no sourcesMarkdown, return empty
    if (!message.sourcesMarkdown) {
      console.log("No sourcesMarkdown found in message");
      return [];
    }
    
    // Check if sourcesMarkdown is already a parsed object
    if (typeof message.sourcesMarkdown === 'object' && message.sourcesMarkdown !== null) {
      // If it has pdf_elements, use those directly
      if (Array.isArray(message.sourcesMarkdown.pdf_elements)) {
        const sourceElements = message.sourcesMarkdown.pdf_elements.map(elem => ({
          title: elem.name || '',
          content: elem.content || ''
        }));
        console.log("Extracted source elements from pdf_elements:", sourceElements);
        return sourceElements;
      }
      // Otherwise return empty
      console.log("sourcesMarkdown is an object but has no pdf_elements");
      return [];
    }
    
    // Otherwise, parse from markdown string
    console.log("Parsing sources from markdown string:", message.sourcesMarkdown.substring(0, 100) + "...");
    return parseSourcesMarkdown(message.sourcesMarkdown);
  };

  // Update the toggleMessageSources function to refresh source counts
  const toggleMessageSources = (messageId) => {
    // Toggle the message's source dropdown
    setExpandedMessageSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
    
    // Force refresh source count whenever dropdown is toggled
    // Get the current message and update the sources count
    const msg = messages[messageId];
    if (msg && msg.sender === 'bot') {
      const sources = getSourcesFromMessage(msg);
      
      // If we have sources, make sure they're properly counted
      if (sources.length > 0) {
        // Find the corresponding question number
        const questionNumber = messages.slice(0, messageId).filter(m => m.sender === 'user').length;
        
        // Update sourcesByQuestion to ensure we have the latest sources
        setSourcesByQuestion(prev => {
          const updated = { ...prev };
          if (!updated[questionNumber]) {
            updated[questionNumber] = [];
          }
          
          // Add any missing sources to the question
          const currentTitles = new Set(updated[questionNumber].map(s => s.title));
          let addedNew = false;
          
          sources.forEach(source => {
            if (!currentTitles.has(source.title)) {
              updated[questionNumber].push(source);
              addedNew = true;
            }
          });
          
          // Only return a new object if we actually changed something
          return addedNew ? updated : prev;
        });
      }
    }
    
    // Force recalculation of source count
    setTimeout(() => {
      // Use setTimeout to ensure this runs after state updates
      const total = calculateTotalSources();
      console.log("Source count updated after toggle:", total);
    }, 0);
  };

  // Toggle main sources panel
  const toggleSourcesPanel = () => {
    setExpandedSources(!expandedSources);
  };

  // Update the initial processing step during component mount as well
  useEffect(() => {
    // Process initial messages to identify which ones have sources
    if (messages.length > 0) {
      let processedMessages = [];
      let initialSourceStates = {};
      
      // Check existing messages for sources
      processedMessages = messages.map((msg, index) => {
        // Ensure message has all required properties for styling
        const normalizedMsg = {
          ...msg,
          // Ensure sender is either 'user', 'bot', or 'sources'
          sender: msg.sender || (msg.role === 'user' ? 'user' : 'bot'),
          // Ensure content exists
          content: msg.content || msg.text || "",
        };
        
        // If this is a bot message and the next message is a sources message,
        // mark it as having sources
        const hasFollowingSources = index < messages.length - 1 && 
                                   messages[index + 1]?.sender === 'sources';
        
        if (normalizedMsg.sender === 'bot') {
          // Check if the message already has hasSources flag
          if (normalizedMsg.hasSources !== undefined) {
            // Initialize expansion state for this message
            initialSourceStates[index] = false;
            return normalizedMsg; // Keep existing flags
          }
          
          // Otherwise, look for adjacent sources
          if (hasFollowingSources) {
            // Initialize expansion state for this message
            initialSourceStates[index] = false;
            return {
              ...normalizedMsg,
              hasSources: true,
              sourcesMarkdown: messages[index + 1].content
            };
          }
        }
        
        // For non-bot messages or those without sources, return normalized message
        return normalizedMsg;
      });
      
      // Filter out standalone sources messages that we've now incorporated into bot messages
      processedMessages = processedMessages.filter((msg, index) => {
        // Keep if not a sources message or if it's not immediately after a bot message
        return msg.sender !== 'sources' || 
              index === 0 || 
              processedMessages[index - 1]?.sender !== 'bot';
      });
      
      // Update messages and expansion states
      setMessages(processedMessages);
      setExpandedMessageSources(initialSourceStates);
    }
  }, []); // Only run once on component mount

  // Update the toggle function to handle the 'all' prefix for the dropdown
  const toggleIndividualSource = (questionNumber, sourceIndex) => {
    const key = `${questionNumber}-${sourceIndex}`;
    setExpandedIndividualSources(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Add toggle function for questions
  const toggleQuestion = (questionNumber) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [questionNumber]: !prev[questionNumber]
    }));
  };

  // Update the function to parse sources markdown while ignoring the header
  const parseSourcesMarkdown = (markdown) => {
    if (!markdown) {
      console.log("No markdown content to parse");
      return [];
    }
    
    console.log("Parsing markdown:", markdown);
    
    // First, extract any direct pdf_elements if they exist in the message data
    // This can happen if the full source object is passed instead of just markdown
    if (typeof markdown === 'object' && markdown.pdf_elements) {
      console.log("Found pdf_elements directly in source data");
      return markdown.pdf_elements.map(elem => ({
        title: elem.name || "Unnamed Source",
        content: elem.content || "No content available" 
      }));
    }
    
    // First, remove the header if present
    let cleanedMarkdown = markdown;
    if (cleanedMarkdown.includes('**Relevant Sources and Extracted Paragraphs:**')) {
      cleanedMarkdown = cleanedMarkdown.split('**Relevant Sources and Extracted Paragraphs:**')[1].trim();
    }
    
    // NEW APPROACH: Look for the specific pattern: "**Source:** **Actual Title**"
    // This format is coming directly from the database
    const sourceMatches = cleanedMarkdown.match(/\*\*Source:\*\*\s+\*\*([^*]+)\*\*/g);
    if (sourceMatches && sourceMatches.length > 0) {
      //console.log("Found source titles in specific format:", sourceMatches);
      
      // Split the markdown into sections by the source pattern
      const sections = cleanedMarkdown.split(/\*\*Source:\*\*\s+\*\*[^*]+\*\*/);
      
      // Process each section, matching it with the corresponding source title
      const sources = [];
      sourceMatches.forEach((match, index) => {
        // Extract the title from the match pattern
        const titleMatch = match.match(/\*\*Source:\*\*\s+\*\*([^*]+)\*\*/);
        let title = "Document";
        if (titleMatch && titleMatch[1]) {
          title = titleMatch[1].trim();
        }
        
        // Get the corresponding content section (skip the first section which appears before any source)
        let content = sections[index + 1] || "";
        
        // Extract text after "Extracted Paragraph:"
        if (content.includes('**Extracted Paragraph:**')) {
          content = content.split('**Extracted Paragraph:**')[1].trim();
        }
        
        // Skip if content is too short
        if (content.length >= 5) {
          sources.push({ title, content });
        }
      });
      
      console.log(`Parsed ${sources.length} sources using specific format:`, sources);
      return sources;
    }
    
    // If the specific pattern wasn't found, fall back to previous approach
    let sections = cleanedMarkdown.split(/\*\*Source \d+:\*\*/);
    
    // If no sources found with the first pattern, try an alternative
    if (sections.length <= 1) {
      // Look for other patterns that might indicate sources
      sections = cleanedMarkdown.split(/\*\*(?:Source|Document|Reference|File)[ :][^*]+\*\*/i);
      console.log("Using alternative split pattern, found sections:", sections.length);
    }
    
    // Process each section (skip the first if empty as it's before the first source)
    const sources = sections
      .map((section, index) => {
        // Skip empty sections and the first section (which is empty or contains the header)
        if (!section.trim() || (index === 0 && !section.includes('**'))) {
          return null;
        }
        
        // Try to extract title from the section - SIMPLIFIED APPROACH
        let title = `Document ${index}`;  // Default title
        
        // Look for title in bold - simplified pattern
        const titleMatch = section.match(/\*\*([^*]+?)\*\*/);
        if (titleMatch) {
          title = titleMatch[1].trim();
          
          // Remove any "Source X:" prefix if present
          title = title.replace(/^Source\s+\d+:\s*/i, '').trim();
          
          console.log(`Extracted title: "${title}" from section`, section.substring(0, 100) + "...");
        }
        
        // Get content after any "Extracted Paragraph:" marker or use the whole section
        let content = section;
        if (content.includes('**Extracted Paragraph:**')) {
          content = content.split('**Extracted Paragraph:**')[1].trim();
        }
        
        // Make sure content isn't too short
        if (content.length < 5) {
          return null;
        }
        
        return { title, content };
      })
      .filter(Boolean); // Remove null entries
    
    console.log(`Parsed ${sources.length} sources from markdown:`, sources);
    return sources;
  };

  // Add function to handle stopping generation
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  // Update the toggleSourcesDropdown function to work with our new flexbox layout
  const toggleSourcesDropdown = useCallback(() => {
    // If we're opening the dropdown, refresh all the source data first
    if (!showSourcesDropdown) {
      console.log("Refreshing sources data before showing dropdown");
      
      // Get the current question number (total user messages)
      const currentQuestionNumber = messages.filter(msg => msg.sender === 'user').length;
      console.log("Current question number:", currentQuestionNumber);
      
      // Force refresh all sources from messages
      const tempSourcesByQuestion = {};
      const allMessageSources = [];
      
      // Collect all sources from messages
      messages.forEach((msg, idx) => {
        if (msg.sender === 'bot' && (msg.hasSources || msg.sourcesMarkdown || (msg.sources && msg.sources.length > 0))) {
          // Find the corresponding user message index
          const prevUserMsgs = messages.slice(0, idx).filter(m => m.sender === 'user').length;
          const questionNum = prevUserMsgs;
          
          // Get sources from this message
          const sources = msg.sources || 
                         (msg.sourcesMarkdown ? parseSourcesMarkdown(msg.sourcesMarkdown) : []);
          
          if (sources.length > 0) {
            console.log(`Found ${sources.length} sources for question ${questionNum}`);
            
            // Ensure this question has an entry
            if (!tempSourcesByQuestion[questionNum]) {
              tempSourcesByQuestion[questionNum] = [];
            }
            
            // Add each source, avoiding duplicates
            sources.forEach(source => {
              if (source && source.title) {
                const existingSource = tempSourcesByQuestion[questionNum].find(s => s.title === source.title);
                if (!existingSource) {
                  tempSourcesByQuestion[questionNum].push(source);
                  allMessageSources.push(source);
                }
              }
            });
          }
        }
      });
      
      // Update sourcesByQuestion with refreshed data
      if (Object.keys(tempSourcesByQuestion).length > 0) {
        console.log("Setting refreshed sourcesByQuestion:", tempSourcesByQuestion);
        setSourcesByQuestion(tempSourcesByQuestion);
        
        // Auto-expand the current question
        setExpandedQuestions(prev => {
          const updated = { ...prev };
          // Collapse all questions first
          Object.keys(updated).forEach(key => {
            updated[key] = false;
          });
          // Then expand the current question if it exists
          if (tempSourcesByQuestion[currentQuestionNumber]) {
            updated[currentQuestionNumber] = true;
          }
          return updated;
        });
      }
      
      // Refresh allUniqueSources
      if (allMessageSources.length > 0) {
        // De-duplicate by title
        const uniqueTitles = new Set();
        const uniqueSources = [];
        allMessageSources.forEach(source => {
          if (source && source.title && !uniqueTitles.has(source.title)) {
            uniqueTitles.add(source.title);
            uniqueSources.push(source);
          }
        });
        
        console.log(`Setting ${uniqueSources.length} unique sources`);
        setAllUniqueSources(uniqueSources);
      }
      
      // Update sources count
      const total = calculateTotalSources();
      setSourcesCount(total);
      
      // Force UI refresh
      setForceUpdate(prev => prev + 1);
      
      // Scroll to the current question after we show the panel
      setTimeout(() => {
        // First find the question element by its ID
        const questionElement = document.getElementById(`question-${currentQuestionNumber}`);
        if (questionElement && sourcesDropdownRef.current) {
          console.log("Scrolling to current question:", currentQuestionNumber);
          
          // Scroll the container to the question element
          sourcesDropdownRef.current.scrollTop = questionElement.offsetTop - 20;
        }
      }, 300);
    }
    
    // Toggle the dropdown visibility
    setShowSourcesDropdown(prev => !prev);
  }, [messages, showSourcesDropdown]);

  // Add a useEffect to process initial messages and extract sources on component mount
  useEffect(() => {
    // Process initial chat history to find sources if they exist
    if (messages.length > 0) {
      console.log("Checking initial messages for sources:", messages.length);
      
      // Create a temporary structure to hold sources by question
      const tempSourcesByQuestion = {};
      let questionCounter = 0;
      
      // Process messages in order
      messages.forEach((msg, index) => {
        if (msg.sender === 'user') {
          // Increment question counter for each user message
          questionCounter++;
        } else if (msg.sender === 'bot' && msg.hasSources) {
          console.log(`Found source in message ${index} for question ${questionCounter}:`, msg.sourcesMarkdown);
          // Parse sources for this bot message
          const parsedSources = parseSourcesMarkdown(msg.sourcesMarkdown);
          
          // Add to the temporary structure
          if (parsedSources.length > 0) {
            if (!tempSourcesByQuestion[questionCounter]) {
              tempSourcesByQuestion[questionCounter] = [];
            }
            
            // Add sources, avoiding duplicates
            const currentTitles = new Set(tempSourcesByQuestion[questionCounter].map(s => s.title));
            parsedSources.forEach(source => {
              if (!currentTitles.has(source.title)) {
                tempSourcesByQuestion[questionCounter].push(source);
              }
            });
          }
        }
      });
      
      // Update state with grouped sources
      if (Object.keys(tempSourcesByQuestion).length > 0) {
        console.log("Setting sources by question:", tempSourcesByQuestion);
        setSourcesByQuestion(tempSourcesByQuestion);
        
        // Initialize expanded state for each question
        const initialExpandedQuestions = {};
        Object.keys(tempSourcesByQuestion).forEach(questionNum => {
          initialExpandedQuestions[questionNum] = false;
        });
        setExpandedQuestions(initialExpandedQuestions);
        
        // Also keep a flattened list of all sources
        const allSources = Object.values(tempSourcesByQuestion).flat();
        console.log("Setting all unique sources:", allSources);
        setAllUniqueSources(allSources);
      }
    }
  }, [messages.length]); // Run when messages change

  // Add this new useEffect hook to update the sources button after sources are fetched
  useEffect(() => {
    // This useEffect will run whenever sourceContent, sourcesByQuestion, or allUniqueSources changes
    // It forces a recalculation of the total source count whenever any source-related state changes
    if (messages.length > 0 && (sourceContent || Object.keys(sourcesByQuestion).length > 0)) {
      console.log("Sources data changed, updating sources count");
      // Force a state update to trigger re-render of the sources button
      const totalSources = calculateTotalSources();
      console.log(`Updated sources count: ${totalSources}`);
      
      // Force a minimal state update to ensure UI refreshes
      setMessages(prevMessages => [...prevMessages]);
    }
  }, [sourceContent, sourcesByQuestion, allUniqueSources]);

  // Modify the calculateTotalSources function to be more thorough
  const calculateTotalSources = () => {
    let total = 0;
    
    // First, count sources from the sourcesByQuestion object
    Object.values(sourcesByQuestion).forEach(sourcesArray => {
      if (Array.isArray(sourcesArray)) {
        total += sourcesArray.length;
      }
    });
    
    // Then, also check messages directly for any sources we might have missed
    messages.forEach(msg => {
      if (msg.sender === 'bot') {
        // Check for sources in various possible locations
        if (msg.sources && Array.isArray(msg.sources)) {
          // Only count sources that weren't already counted via sourcesByQuestion
          msg.sources.forEach(source => {
            if (source && source.title) {
              // Check if this source is already counted in sourcesByQuestion
              let isDuplicate = false;
              Object.values(sourcesByQuestion).forEach(sourcesArray => {
                if (Array.isArray(sourcesArray) && 
                    sourcesArray.some(s => s.title === source.title)) {
                  isDuplicate = true;
                }
              });
              
              if (!isDuplicate) {
                total += 1;
              }
            }
          });
        }
        
        // Also check if message has sourcesMarkdown but no parsed sources yet
        if (msg.sourcesMarkdown && !msg.sources && (!msg.hasSources || msg.hasSources === true)) {
          // Try to parse sources from markdown
          const parsedSources = parseSourcesMarkdown(msg.sourcesMarkdown);
          if (parsedSources.length > 0) {
            // Check for duplicates before counting
            parsedSources.forEach(source => {
              if (source && source.title) {
                let isDuplicate = false;
                Object.values(sourcesByQuestion).forEach(sourcesArray => {
                  if (Array.isArray(sourcesArray) && 
                      sourcesArray.some(s => s.title === source.title)) {
                    isDuplicate = true;
                  }
                });
                
                if (!isDuplicate) {
                  total += 1;
                }
              }
            });
          }
        }
      }
    });
    
    // Also check if sourceContent has unparsed sources
    if (sourceContent && sourceContent.length > 0) {
      const unparsedSources = parseSourcesMarkdown(sourceContent);
      if (unparsedSources.length > 0) {
        // Check for duplicates
        unparsedSources.forEach(source => {
          if (source && source.title) {
            let isDuplicate = false;
            
            // Check against sourcesByQuestion
            Object.values(sourcesByQuestion).forEach(sourcesArray => {
              if (Array.isArray(sourcesArray) && 
                  sourcesArray.some(s => s.title === source.title)) {
                isDuplicate = true;
              }
            });
            
            // Check against messages
            messages.forEach(msg => {
              if (msg.sender === 'bot' && msg.sources) {
                if (msg.sources.some(s => s.title === source.title)) {
                  isDuplicate = true;
                }
              }
            });
            
            if (!isDuplicate) {
              total += 1;
            }
          }
        });
      }
    }
    
    return total;
  };

  // Create a dedicated useEffect to refresh sources after a bot message is added
  useEffect(() => {
    // Check if the most recent message is from the bot
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.sender === 'bot') {
      console.log("New bot message detected, refreshing sources data");
      
      // Force recalculation of total sources
      const total = calculateTotalSources();
      console.log("Total sources after new message:", total);
      
      // Check if this bot message should have sources
      if (lastMessage.sourcesMarkdown || (lastMessage.sources && lastMessage.sources.length > 0)) {
        // If sources are already attached but not showing, try to force-set hasSources
        if (!lastMessage.hasSources) {
          console.log("Fixing missing hasSources flag on message");
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              hasSources: true
            };
            return updated;
          });
        }
        
        // Force refresh of sources in the All Sources dropdown
        const parsedSources = lastMessage.sources || 
                             (lastMessage.sourcesMarkdown ? 
                              parseSourcesMarkdown(lastMessage.sourcesMarkdown) : 
                              []);
        
        if (parsedSources.length > 0) {
          console.log("Refreshing All Sources dropdown with new sources:", parsedSources);
          
          // Count the number of user messages to determine the question number
          const questionNumber = messages.filter(msg => msg.sender === 'user').length;
          
          // Update sourcesByQuestion with the new sources
          setSourcesByQuestion(prev => {
            const updated = { ...prev };
            if (!updated[questionNumber]) {
              updated[questionNumber] = [];
            }
            
            // Add the new sources, avoiding duplicates
            const currentTitles = new Set(updated[questionNumber].map(s => s.title));
            parsedSources.forEach(source => {
              if (!currentTitles.has(source.title)) {
                updated[questionNumber].push(source);
              }
            });
            
            return updated;
          });
          
          // Also update allUniqueSources for the dropdown
          setAllUniqueSources(prevSources => {
            // Create a Set with current titles for easy duplicate checking
            const currentSourceTitles = new Set(prevSources.map(source => source.title));
            
            // Filter out sources we already have
            const newSources = parsedSources.filter(source => !currentSourceTitles.has(source.title));
            
            console.log(`Adding ${newSources.length} new unique sources to dropdown`);
            
            // Return updated array with new unique sources added
            return [...prevSources, ...newSources];
          });
          
          // Optionally auto-show the sources dropdown if we found new sources
          // Uncomment this if you want to auto-show the dropdown
          /*
          if (!showSourcesDropdown) {
            setShowSourcesDropdown(true);
          }
          */
        }
      }
    }
  }, [messages.length]); // Run when messages array length changes

  // Add a helper function to format question labels
  const getQuestionLabel = (questionNumber) => {
    // Find the corresponding user message
    const userMessages = messages.filter(msg => msg.sender === 'user');
    if (userMessages.length >= questionNumber && userMessages[questionNumber - 1]) {
      const questionText = userMessages[questionNumber - 1].content;
      // Split the question into words and take first 4
      const words = questionText.split(/\s+/);
      const firstFourWords = words.slice(0, 4).join(' ');
      return `${firstFourWords}${words.length > 4 ? '...' : ''}`;
    }
    // Fallback to number if question text not found
    return `Question ${questionNumber}`;
  };

  // Add a new useEffect to force update the lastInteractionData when needed
  useEffect(() => {
    // Check if messages exist but lastInteractionData is null or undefined
    const lastBotMessage = messages.filter(msg => msg.sender === 'bot').pop();
    const lastUserMessage = messages.filter(msg => msg.sender === 'user').pop();
    
    if (lastBotMessage && lastUserMessage && !lastInteractionData && !isGenerating) {
      console.log("FORCE UPDATE: Restoring lastInteractionData for feedback buttons");
      
      // Create a new interaction data object from the last messages
      const forcedInteractionData = {
        question: lastUserMessage.content,
        answer: lastBotMessage.content,
        sources: lastBotMessage.sources || [],
        sourcesMarkdown: lastBotMessage.sourcesMarkdown || '',
        model: selectedModel,
        temperature: temperature, 
        dataset: dataset,
        personality: persona,
        chat_id: selectedChat,
        elapsed_time: 0, // Default since we don't have the real value
        messageIndex: messages.indexOf(lastBotMessage)
      };
      
      // Force update the lastInteractionData
      setLastInteractionData(forcedInteractionData);
    }
  }, [messages, lastInteractionData, isGenerating]);

  // Also modify our aggressive refresh timeout to ensure lastInteractionData is restored
  // At the end of the timeout function we added previously, add this code:

  // Find and update this section in the timeout function already added
  setTimeout(() => {
    // ... existing code from before ...
    
    // Add this at the end of the timeout function:
    
    // Also ensure feedback buttons are enabled by restoring lastInteractionData if needed
    if (!lastInteractionData) {
      const lastBotMsg = messages.filter(msg => msg.sender === 'bot').pop();
      const lastUserMsg = messages.filter(msg => msg.sender === 'user').pop();
      
      if (lastBotMsg && lastUserMsg) {
        const forcedInteractionData = {
          question: lastUserMsg.content,
          answer: lastBotMsg.content,
          sources: lastBotMsg.sources || [],
          sourcesMarkdown: lastBotMsg.sourcesMarkdown || '',
          model: selectedModel,
          temperature: temperature,
          dataset: dataset,
          personality: persona,
          chat_id: selectedChat,
          elapsed_time: 0,
          messageIndex: messages.indexOf(lastBotMsg)
        };
        
        console.log("FORCE ENABLING FEEDBACK BUTTONS");
        setLastInteractionData(forcedInteractionData);
      }
    }
  }, 500);

  // Add a useEffect that updates sourcesCount whenever relevant data changes
  useEffect(() => {
    // Update the sourcesCount state whenever sources change
    const total = calculateTotalSources();
    setSourcesCount(total);
    
    // Force a re-render of the entire component to ensure all UI elements update
    setTimeout(() => setForceUpdate(prev => prev + 1), 100);
  }, [messages, sourceContent, sourcesByQuestion, allUniqueSources, forceUpdate]);

  // Add useEffect hook for Persona -> Dataset logic (around line 1080)
  useEffect(() => {
    console.log(`[useEffect Persona->Dataset] Persona changed to: ${persona}`);
    let newDataset = dataset; // Start with current dataset
    let shouldLock = false;

    if (persona === "Assistant") {
      newDataset = "KG";
      shouldLock = true;
      console.log("Setting dataset to KG and locking.");
    } else if (persona === "General Schedule GS") {
      newDataset = "GS";
      shouldLock = true;
      console.log("Setting dataset to GS and locking.");
    } else if (persona === "Air Force") {
      newDataset = "Air Force";
      shouldLock = true;
      console.log("Setting dataset to Air Force and locking.");
    } else if ([ "Researcher", "Analyst", "Strategist"].includes(persona)) {
      newDataset = "None";
      shouldLock = true;
      console.log("Setting dataset to None and locking.");
    } else if (persona === "None") {
       // Explicitly unlock if persona is None
       shouldLock = false;
       console.log("Persona is None, unlocking dataset.");
       // Keep current dataset when switching to None persona
    }
    // No need for an else, keeps current dataset and lock status for unknown personas

    // Only update state if values actually change to prevent infinite loops
    if (dataset !== newDataset) {
        setDataset(newDataset);
    }

  }, [persona]); // Rerun when persona changes

  // Modify the useEffect hook for Dataset -> Persona logic (around line 1110)
  useEffect(() => {
    console.log(`[useEffect Dataset->Persona] Dataset changed to: ${dataset}`);
    // Define personas allowed ONLY when dataset is 'None'
    const noneDatasetPersonas = ["None", "Researcher", "Analyst", "Strategist"]; 
    let allowedPersonas = []; // Start with empty list

    if (dataset === "KG") {
      allowedPersonas = ["Assistant"]; // Only Assistant for KG
      console.log("Dataset is KG, limiting personas to:", allowedPersonas);
    } else if (dataset === "GS") {
      allowedPersonas = ["General Schedule GS"]; // Only GS for GS
      console.log("Dataset is GS, limiting personas to:", allowedPersonas);
    } else if (dataset === "Air Force") {
      allowedPersonas = ["Air Force"]; // Only Air Force for Air Force
      console.log("Dataset is Air Force, limiting personas to:", allowedPersonas);
    } else if (dataset === "None"){
      // If dataset is None, allow the designated 'noneDatasetPersonas'
      allowedPersonas = noneDatasetPersonas;
      console.log("Dataset is None, allowing personas:", allowedPersonas);
    }
    
    // Update the displayable personas
    // Make sure the allowed list isn't empty before setting
    if (allowedPersonas.length > 0) {
        setDisplayablePersonas(allowedPersonas);
    } else {
         // Fallback: if dataset is unknown, allow all (or just None? Decide policy)
         console.warn(`Unknown dataset '${dataset}', falling back to allowing all personas.`);
         setDisplayablePersonas(availablePersonas);
    }
    
    // Check if the current persona is still valid within the NEWLY allowed list
    if (!allowedPersonas.includes(persona)) {
      console.log(`Current persona '${persona}' is not compatible with dataset '${dataset}'. Resetting persona.`);
      // Reset to the *first* allowed persona for the current dataset, or None if dataset is None
      const newDefaultPersona = dataset === "None" ? "None" : (allowedPersonas[0] || "None");
      console.log(`Setting new default persona to: ${newDefaultPersona}`);
      setPersona(newDefaultPersona);
      // The other useEffect [persona] might trigger to adjust dataset lock if needed
    }

  }, [dataset, availablePersonas]); // Rerun when dataset or the full list of availablePersonas changes

  // Add this new function to handle copying message text
  const handleCopyMessage = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setSnackbarMessage("Copied!");
        setSnackbarOpen(true);
      })
      .catch(err => {
        console.error('Failed to copy text:', err);
      });
  };

  // Function to show feedback notification
  const showFeedbackNotification = () => {
    setSnackbarMessage("Thank you for the Feedback!");
    setSnackbarSeverity('success');
    setSnackbarOpen(true);
  };

  // Load hidden chats from localStorage on component mount
  useEffect(() => {
    const storedHiddenChats = localStorage.getItem('hiddenChats');
    if (storedHiddenChats) {
      try {
        setHiddenChats(JSON.parse(storedHiddenChats));
      } catch (error) {
        console.error("Error parsing hidden chats from localStorage:", error);
        localStorage.removeItem('hiddenChats');
      }
    }
  }, []);

  // Function to hide a chat
  const handleHideChat = (chatId, event) => {
    // Stop the click event from bubbling up to the button
    event.stopPropagation();

    console.log(`Hiding chat with ID: ${chatId}`);
    const updatedHiddenChats = [...hiddenChats, chatId];
    setHiddenChats(updatedHiddenChats);
    localStorage.setItem('hiddenChats', JSON.stringify(updatedHiddenChats));
    console.log(`Updated hidden chats: ${JSON.stringify(updatedHiddenChats)}`);
  };
  
  // Function to unhide a chat
  const handleUnhideChat = (chatId) => {
    console.log(`Unhiding chat with ID: ${chatId}`);
    const updatedHiddenChats = hiddenChats.filter(id => id !== chatId);
    setHiddenChats(updatedHiddenChats);
    localStorage.setItem('hiddenChats', JSON.stringify(updatedHiddenChats));
  };
  
  // Function to show all hidden chats
  const handleShowAllHiddenChats = () => {
    console.log(`Showing all ${hiddenChats.length} hidden chats`);
    setHiddenChats([]);
    localStorage.removeItem('hiddenChats');
  };

  useEffect(() => {
    // Remove the calls to fetchChatHistories, fetchPersonas, and fetchUserPreferences
    // as they're already called elsewhere in the component
    
    // Set up polling to check if user account is still active
    const checkUserStatusInterval = setInterval(() => {
      fetch('https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': sessionToken
        }
      })
      .then(response => {
        if (!response.ok) {
          // If response is not OK (401, 403, etc.), log the user out
          console.log('User account check failed, logging out');
          localStorage.removeItem('session_token');
          window.location.href = 'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/signin';
        }
        return response.json();
      })
      .catch(error => {
        console.error('Error checking user status:', error);
        // On error, also log out for safety
        localStorage.removeItem('session_token');
        window.location.href = 'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/signin';
      });
    }, 30000); // Check every 30 seconds
    
    // Clean up interval on component unmount
    return () => {
      clearInterval(checkUserStatusInterval);
    };
  }, [sessionToken]); // Added sessionToken to dependencies

  return (
    <AppTheme>
      <CssBaseline />
      <Box sx={{ position: 'fixed', top: '1rem', right: '1rem', display: 'flex', alignItems: 'center', gap: 2, zIndex: 1300 }}>
   {/* Readme Button placed horizontally next to Logout */}
   <Button
              variant="outlined"
              onClick={() => setOpenReadme(true)}
              sx={{
                 padding: '8px 16px',
                backgroundColor: '#0D1B2A',
                color: '#FFFFFF',
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: '#1B263B',
                },
              }}
            >
              Readme
            </Button>
        <ColorModeSelect />
        {isLoggedIn && (
          <>
            <Button
              color="primary"
              variant="contained"
              size="small"
              onClick={handleLogout}
              sx={{
                padding: '8px 16px',
                backgroundColor: '#0D1B2A',
                color: '#FFFFFF',
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: '#1B263B',
                },
              }}
            >
              Logout
            </Button>
          </>
        )}
      </Box>
      
      {/* Readme Dialog */}
      <Dialog open={openReadme} onClose={() => setOpenReadme(false)} maxWidth="md" fullWidth>
        {/* Dialog Title with black background */}
        <DialogTitle sx={{ backgroundColor: '#000000', color: '#FFFFFF' }}>
          Readme
        </DialogTitle>
        {/* Dialog Content with navy background */}
        <DialogContent dividers sx={{ backgroundColor: '#0D1B2A', color: '#FFFFFF' }}>
          <ReactMarkdown>{readmeText}</ReactMarkdown>
        </DialogContent>
        {/* Dialog Actions with black background */}
        <DialogActions sx={{ backgroundColor: '#000000' }}>
          <Button 
            onClick={() => setOpenReadme(false)} 
            sx={{ color: '#FFFFFF' }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
      {/* New Chat Dialog */}
      <Dialog open={newChatDialogOpen} onClose={() => setNewChatDialogOpen(false)}>
        <DialogTitle>Name Your New Chat</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Chat Title"
            fullWidth
            value={newChatTitle}
            onChange={(e) => setNewChatTitle(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewChatDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateChat}>Create Chat</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for settings confirmation and warnings */}
      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbarSeverity}
          sx={{
            width: '100% !important',
            backgroundColor: 'white !important',
            color: 'black !important',
            fontWeight: 'bold !important',
            border: '1px solid #ddd !important',
            '& .MuiAlert-icon': {
              color: 'black !important'
            },
            '& .MuiAlert-message': {
              fontWeight: 'bold !important'
            },
            '&.MuiAlert-standardSuccess': {
              backgroundColor: 'white !important',
              border: '1px solid #ddd !important'
            },
            '&.MuiAlert-standardError': {
              backgroundColor: 'white !important',
              border: '1px solid #ddd !important'
            }
          }}
        >
          {snackbarMessage || "Settings Confirmed"}
        </Alert>
      </Snackbar>

      <div className="outer-container" style={{
        display: 'flex',
        flexDirection: 'row',
        height: 'calc(100vh - 80px)',
        width: '100%',
        marginTop: '70px',
        paddingBottom: '10px',
        paddingLeft: '10px',
        paddingRight: '10px',
        boxSizing: 'border-box',
        backgroundColor: '#000000',
        gap: '10px',
        overflow: 'hidden',
        position: 'relative',
        // Add transition for smooth resizing
        transition: 'all 0.3s ease-in-out'
      }}>
        {/* Sidebar for Chat Histories - use flex proportion */}
        <Box
          sx={{
            // Use flex proportions instead of fixed width
            flex: showSourcesDropdown ? '0 0 20%' : '0 0 25%', // smaller when sources shown
            minWidth: { xs: '150px', sm: '180px' }, // Minimum width for usability
            maxWidth: '250px', // Maximum width to prevent excessive sizing
            borderRight: '1px solid #1B263B',
            overflowY: 'auto',
            overflowX: 'hidden',
            p: 1,
            textAlign: 'center',
            backgroundColor: '#121212',
            borderRadius: '12px',
            boxShadow: '0 3px 6px rgba(0,0,0,0.2)',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            transition: 'flex 0.3s ease-in-out', // Smooth transition
            '& button': {
              fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' },
              padding: { xs: '4px', sm: '6px', md: '8px' }
            }
          }}
        >
          <Box component="h3" sx={{ m: 0, p: '10px 0', color: '#E0E1DD' }}>Chat Histories</Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, gap: '4px' }}>
            <Tooltip title="New Chat" arrow>
              <Button
                variant="contained"
                color="inherit"
                onClick={handleNewChat}
                sx={{
                  backgroundColor: '#0D1B2A',
                  color: '#FFFFFF',
                  fontWeight: 'bold',
                  textTransform: 'none',
                  padding: '6px 8px',
                  minWidth: '110px',
                  width: '110px',
                  height: '32px',
                  display: 'flex',
                  justifyContent: 'center',
                  '&:hover': {
                    backgroundColor: '#1B263B',
                  },
                }}
              >
                <AddIcon />
              </Button>
            </Tooltip>
            
            {/* Show hidden chats button, always visible */}
            <Tooltip title="Show all hidden chats" arrow>
              <Button
                variant="contained"
                color="inherit"
                onClick={handleShowAllHiddenChats}
                sx={{
                  backgroundColor: '#0D1B2A',
                  color: '#FFFFFF',
                  fontWeight: 'bold',
                  textTransform: 'none',
                  fontSize: '0.65rem',
                  padding: '6px 8px',
                  minWidth: '110px',
                  height: '32px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  '&:hover': {
                    backgroundColor: '#1B263B',
                  },
                }}
              >
                Show Hidden ({hiddenChats.length})
              </Button>
            </Tooltip>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {chatHistories
              .filter(chat => !hiddenChats.includes(chat.id)) // Filter out hidden chats
              .map(chat => (
                <Box 
                  key={chat.id} 
                  sx={{ 
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  onMouseEnter={() => setHoveredButtonId(chat.id)}
                  onMouseLeave={() => setHoveredButtonId(null)}
                >
                  <Button
                    variant="contained"
                    color="inherit"
                    onClick={() => handleSelectChat(chat.id)}
                    sx={{
                      backgroundColor: '#0D1B2A',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      textTransform: 'none',
                      width: '100%',
                      '&:hover': {
                        backgroundColor: '#1B263B',
                      },
                    }}
                  >
                    {chat.title || chat.id}
                  </Button>
                  {/* Hide button only shows on hover */}
                  {hoveredButtonId === chat.id && (
                    <Box 
                      sx={{
                        position: 'absolute',
                        right: '8px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        cursor: 'pointer',
                        color: '#fff',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '50%',
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        '&:hover': {
                          color: '#fff',
                          backgroundColor: 'rgba(255,255,255,0.4)',
                        },
                      }}
                      onClick={(e) => handleHideChat(chat.id, e)}
                      title="Hide chat"
                    >
                      ×
                    </Box>
                  )}
                </Box>
              ))}
          </Box>
        </Box>

        {/* Main Chat Area - use flex proportion */}
        <div className="chat-messages" style={{
          backgroundColor: '#121212',
          borderRadius: '12px',
          boxShadow: '0 3px 6px rgba(0,0,0,0.2)',
          // Use flex proportions
          flex: showSourcesDropdown ? '1 1 55%' : '1 1 75%', // adjust based on sources visibility
          display: 'flex',
          flexDirection: 'column',
          boxSizing: 'border-box',
          overflow: 'hidden',
          height: '100%',
          minWidth: '300px',
          // Add transition for smooth resizing
          transition: 'flex 0.3s ease-in-out'
        }}>
          {/* Chat header - fixed height */}
          <div className="chat-header" style={{
            backgroundColor: '#0D1B2A',
            borderTopLeftRadius: '12px',
            borderTopRightRadius: '12px',
            padding: '10px 20px',
            flexShrink: 0 // Prevent header from shrinking
          }}>
            <h2 style={{ margin: '10px 0', color: '#E0E1DD' }}> J1 Chat</h2>
          </div>

          {/* Messages area - flexes to fill available space */}
          <div className="messages-display" style={{ 
            padding: '15px', 
            flexGrow: 1,
            overflowY: 'auto',
            overflowX: 'hidden'
          }} ref={messagesContainerRef}>
            {messages.map((msg, index) => (
              <div key={index} style={{ 
                marginBottom: '20px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                width: '100%'
              }}>
                {msg.sender === 'sources' ? (
                  // Render sources as markdown (you can style this block as needed)
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      maxWidth: '75%',
                      minWidth: '200px'
                    }}>
                      {/* Message header with sender name */}
                      <div style={{
                        padding: '8px 15px',
                        borderTopLeftRadius: '15px',
                        borderTopRightRadius: '15px',
                        borderBottomLeftRadius: '0',
                        borderBottomRightRadius: '0',
                        backgroundColor: msg.sender === 'user' ? '#1B263B' : '#0D1B2A',
                        color: '#E0E1DD',
                        fontWeight: 'bold',
                        alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      }}>
                        {msg.sender === 'user' ? username : 'J1 Chat'}
                      </div>
                      
                      {/* Message content */}
                      <div style={{ 
                        padding: '12px 15px',
                        backgroundColor: msg.sender === 'user' ? '#415A77' : '#1B263B',
                        color: '#E0E1DD',
                        borderTopLeftRadius: '0',
                        borderTopRightRadius: '0',
                        borderBottomLeftRadius: '15px',
                        borderBottomRightRadius: '15px',
                        whiteSpace: 'pre-line',
                        overflowWrap: 'break-word',
                        wordBreak: 'break-word',
                        lineHeight: '1.5',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                        position: 'relative' // Keep position relative
                      }}>
                        {msg.content}
                      </div>
                    </div>
                    
                    {/* Copy button for user messages - outside the bubble */}
                    {msg.sender === 'user' && (
                      <div
                        onClick={() => handleCopyMessage(msg.content)}
                        style={{ 
                          alignSelf: 'flex-end',
                          marginTop: '5px',
                          marginRight: '5px',
                          opacity: 1,
                          padding: '4px',
                          fontSize: '14px',
                          cursor: 'pointer',
                          color: '#E0E1DD',
                          backgroundColor: 'rgba(0,0,0,0.3)',
                          borderRadius: '4px',
                          width: '20px',
                          height: '20px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        aria-label="Copy message"
                        title="Copy message"
                      >
                        &#x1F4CB;
                      </div>
                    )}
                    
                    {/* If this is a bot message with attached sources */}
                    {msg.sender === 'bot' && (msg.hasSources || msg.sourcesMarkdown || (msg.sources && msg.sources.length > 0)) && (
                      <div style={{ marginTop: '10px', alignSelf: 'flex-start', maxWidth: '75%', position: 'relative', display: 'flex', alignItems: 'flex-start' }}>
                        {/* Get sources using our helper function */}
                        {(() => {
                          const sources = getSourcesFromMessage(msg);
                          const sourceCount = sources.length;
                          
                          // Add console logs to debug source data
                          console.log(`Message ${index} sources:`, sources);
                          
                          // Exit early if no sources found
                          if (sourceCount === 0) {
                            console.log("No sources found for message", index);
                            return null;
                          }
                          
                          // If only one source, use simplified view
                          if (sourceCount === 1) {
                            return (
                              <>
                                {/* Container with relative positioning to handle button placement */}
                                <div style={{ position: 'relative' }}>
                                  {/* Single source toggle - Changed to show "Source (1)" */}
                                  <div 
                                    onClick={() => toggleMessageSources(index)}
                                    style={{ 
                                      cursor: 'pointer',
                                      border: '1px solid #1B263B',
                                      borderRadius: '4px',
                                      backgroundColor: '#0D1B2A',
                                      color: '#FFFFFF',
                                      padding: '8px 12px',
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'center',
                                      fontSize: '0.9rem',
                                      userSelect: 'none',
                                      transition: 'background-color 0.2s'
                                    }}
                                  >
                                    <span>Source (1)</span>
                                    {expandedMessageSources[index] ? 
                                      <ExpandLessIcon style={{ fontSize: '18px' }} /> : 
                                      <ExpandMoreIcon style={{ fontSize: '18px' }} />
                                    }
                                  </div>

                                  {/* Copy button positioned absolutely to the right of the dropdown */}
                                  <div
                                    onClick={() => handleCopyMessage(msg.content)}
                                    style={{ 
                                      position: 'absolute',
                                      top: '0px',
                                      right: '-28px', // Position it to the right of dropdown
                                      opacity: 1,
                                      padding: '4px',
                                      fontSize: '14px',
                                      cursor: 'pointer',
                                      color: '#E0E1DD',
                                      backgroundColor: 'rgba(0,0,0,0.3)',
                                      borderRadius: '4px',
                                      width: '20px',
                                      height: '20px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center'
                                    }}
                                    aria-label="Copy message"
                                    title="Copy message"
                                  >
                                    &#x1F4CB;
                                  </div>
                                  
                                  {/* Show second dropdown for document title when main dropdown is expanded */}
                                  {expandedMessageSources[index] && (
                                    <div style={{ 
                                      marginTop: '5px',
                                      display: 'flex',
                                      flexDirection: 'column',
                                      gap: '8px',
                                      width: '100%'
                                    }}>
                                      {/* Document title toggle */}
                                      <div 
                                        onClick={() => toggleIndividualSource(index, 0)}
                                        style={{ 
                                          cursor: 'pointer',
                                          border: '1px solid #1B263B',
                                          borderRadius: '4px',
                                          backgroundColor: '#1B263B',
                                          color: '#FFFFFF',
                                          padding: '8px 12px',
                                          display: 'flex',
                                          justifyContent: 'space-between',
                                          alignItems: 'center',
                                          fontSize: '0.9rem',
                                          userSelect: 'none',
                                          transition: 'background-color 0.2s'
                                        }}
                                      >
                                        <span>{sources[0].title || 'Document 1'}</span>
                                        {expandedIndividualSources[`${index}-0`] ? 
                                          <ExpandLessIcon style={{ fontSize: '16px' }} /> : 
                                          <ExpandMoreIcon style={{ fontSize: '16px' }} />
                                        }
                                      </div>
                                      
                                      {/* Only show content when second dropdown is expanded */}
                                      {expandedIndividualSources[`${index}-0`] && (
                                        <div style={{ 
                                          padding: '10px', 
                                          backgroundColor: '#121212', 
                                          color: '#E0E1DD',
                                          borderBottomLeftRadius: '4px',
                                          borderBottomRightRadius: '4px',
                                          maxHeight: '200px',
                                          overflowY: 'auto',
                                          borderLeft: '1px solid #1B263B',
                                          borderRight: '1px solid #1B263B',
                                          borderBottom: '1px solid #1B263B'
                                        }}>
                                          <ReactMarkdown>{sources[0].content}</ReactMarkdown>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </>
                            );
                          } else {
                            // Multiple sources, use nested dropdowns
                            return (
                              <>
                                {/* Container with relative positioning for dropdown and sources */}
                                <div style={{ position: 'relative' }}>
                                  {/* Main dropdown container */}
                                  <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                                    {/* Main sources toggle */}
                                    <div 
                                      onClick={() => toggleMessageSources(index)}
                                      style={{ 
                                        cursor: 'pointer',
                                        border: '1px solid #1B263B',
                                        borderRadius: '4px',
                                        backgroundColor: '#0D1B2A',
                                        color: '#FFFFFF',
                                        padding: '8px 12px',
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        fontSize: '0.9rem',
                                        userSelect: 'none',
                                        transition: 'background-color 0.2s',
                                        width: '100%'
                                      }}
                                    >
                                      <span>Sources ({sourceCount})</span>
                                      {expandedMessageSources[index] ? 
                                        <ExpandLessIcon style={{ fontSize: '18px' }} /> : 
                                        <ExpandMoreIcon style={{ fontSize: '18px' }} />
                                      }
                                    </div>
                                    
                                    {/* Display individual source dropdowns when the main dropdown is expanded */}
                                    {expandedMessageSources[index] && (
                                      <div style={{ 
                                        marginTop: '5px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '8px',
                                        width: '100%'
                                      }}>
                                        {sources.map((source, sourceIndex) => (
                                          <div key={sourceIndex}>
                                            {/* Individual source toggle */}
                                            <div 
                                              onClick={() => toggleIndividualSource(index, sourceIndex)}
                                              style={{ 
                                                cursor: 'pointer',
                                                border: '1px solid #1B263B',
                                                borderRadius: '4px',
                                                backgroundColor: '#1B263B',
                                                color: '#FFFFFF',
                                                padding: '8px 12px',
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                fontSize: '0.9rem',
                                                userSelect: 'none',
                                                transition: 'background-color 0.2s'
                                              }}
                                            >
                                              <span>{source.title || `Document ${sourceIndex + 1}`}</span>
                                              {expandedIndividualSources[`${index}-${sourceIndex}`] ? 
                                                <ExpandLessIcon style={{ fontSize: '16px' }} /> : 
                                                <ExpandMoreIcon style={{ fontSize: '16px' }} />
                                              }
                                            </div>
                                            
                                            {/* Individual source content */}
                                            {expandedIndividualSources[`${index}-${sourceIndex}`] && (
                                              <div style={{ 
                                                padding: '10px', 
                                                backgroundColor: '#121212', 
                                                color: '#E0E1DD',
                                                borderBottomLeftRadius: '4px',
                                                borderBottomRightRadius: '4px',
                                                maxHeight: '200px',
                                                overflowY: 'auto',
                                                borderLeft: '1px solid #1B263B',
                                                borderRight: '1px solid #1B263B',
                                                borderBottom: '1px solid #1B263B'
                                              }}>
                                                <ReactMarkdown>{source.content}</ReactMarkdown>
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {/* Copy button positioned absolutely to the right of the dropdown */}
                                  <div
                                    onClick={() => handleCopyMessage(msg.content)}
                                    style={{ 
                                      position: 'absolute',
                                      top: '0px',
                                      right: '-28px', // Position it to the right of dropdown
                                      opacity: 1,
                                      padding: '4px',
                                      fontSize: '14px',
                                      cursor: 'pointer',
                                      color: '#E0E1DD',
                                      backgroundColor: 'rgba(0,0,0,0.3)',
                                      borderRadius: '4px',
                                      width: '20px',
                                      height: '20px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center'
                                    }}
                                    aria-label="Copy message"
                                    title="Copy message"
                                  >
                                    &#x1F4CB;
                                  </div>
                                </div>
                              </>
                            );
                          }
                        })()}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
          
          {/* Chat controls - fixed height */}
          <div className="chat-controls" style={{ 
            padding: '15px', 
            borderTop: '1px solid #1B263B',
            borderBottomLeftRadius: '12px',
            borderBottomRightRadius: '12px',
            flexShrink: 0 // Prevent controls from shrinking
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Button
                id="modelSelectButton"
                sx={{
                marginRight: '5px',
                backgroundColor: '#0D1B2A',
                color: '#FFFFFF',
                fontWeight: 'bold',
                textTransform: 'none',
                '&:hover': {
                backgroundColor: '#1B263B',
                },
                }}
                onClick={() => setShowModels(prev => !prev)}
              >
                Model: {formatModelName(selectedModel)}
              </Button>
              <Button
                sx={{
                    backgroundColor: '#0D1B2A',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    textTransform: 'none',
                    '&:hover': {
                      backgroundColor: '#1B263B',
                    },
                }}
                onClick={() => setShowSettings(prev => !prev)}
              >
                {showSettings ? 'Hide Settings' : 'Show Settings'}
              </Button>
              <Button
                sx={{
                  backgroundColor: '#0D1B2A',
                  color: '#FFFFFF',
                  fontWeight: 'bold',
                  textTransform: 'none',
                  '&:hover': {
                    backgroundColor: '#1B263B',
                  },
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
                onClick={toggleSourcesDropdown}
              >
                Sources ({sourcesCount}) {showSourcesDropdown ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              </Button>
              <FeedbackButtons
                sessionToken={sessionToken}
                interactionData={lastInteractionData}
                disabled={!lastInteractionData}
              />
            </div>
            {showModels && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-around',
                gap: '20px',
                padding: '10px',
                border: '1px solid #1B263B',
                marginTop: '10px',
                backgroundColor: '#121212',
                borderRadius: '8px'
              }}>
                {availableModels.map(model => (
                  <Button
                    key={model}
                    onClick={() => handleSelectModel(model)}
                    sx={{
                        padding: '8px 16px',
                        backgroundColor: '#0D1B2A',
                        color: '#FFFFFF',
                        fontWeight: 'bold',
                        '&:hover': {
                          backgroundColor: '#1B263B',
                        },
                    }}
                  >
                    {formatModelName(model)} {/* Use formatModelName here */}
                  </Button>
                ))}
              </div>
            )}
            {showSettings && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-around',
                gap: '20px',
                padding: '10px',
                border: '1px solid #1B263B',
                marginTop: '10px',
                backgroundColor: '#121212',
                borderRadius: '8px'
              }}>
                <div>
                  <label>Dataset: </label>
                  <select 
                    value={dataset} 
                    onChange={e => {
                      const newDataset = e.target.value;
                      console.log(`[DEBUG] Dataset dropdown changed to: ${newDataset}`);
                      setDataset(newDataset);
                    }}
                    style={{
                      backgroundColor: '#0D1B2A', // Reverted background color
                      color: '#FFFFFF',
                      border: '1px solid #1B263B',
                      borderRadius: '4px',
                      padding: '8px',
                      height: '40px',
                      fontSize: '16px',
                      outline: 'none',
                      cursor: 'pointer' // Reverted cursor
                    }}
                  >
                    <option value="KG">KG</option>
                    <option value="Air Force">Air Force</option>
                    <option value="GS">GS</option>
                    <option value="None">None</option>
                  </select>
                  {/* Remove hint text */}
                </div>
                <div>
                  <label>Temperature: </label>
                  {/* Style the input number similarly */}
                  <input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="1" 
                    value={temperature} 
                    onChange={e => setTemperature(parseFloat(e.target.value))}
                    style={{
                      backgroundColor: '#0D1B2A',
                      color: '#FFFFFF',
                      border: '1px solid #1B263B',
                      borderRadius: '4px',
                      padding: '8px', 
                      height: '40px',
                      width: '60px', // Adjust width as needed
                      fontSize: '16px',
                      outline: 'none'
                    }}
                  />
                </div>
                <div>
                  <label>Persona: </label>
                  <select 
                    value={persona} 
                    onChange={e => {
                      const newPersona = e.target.value;
                      console.log("[Settings onChange] Persona changed to:", newPersona); 
                      setPersona(newPersona);
                    }}
                    style={{
                      backgroundColor: '#0D1B2A',
                      color: '#FFFFFF',
                      border: '1px solid #1B263B',
                      borderRadius: '4px',
                      padding: '8px', 
                      height: '40px', 
                      fontSize: '16px', 
                      outline: 'none'
                    }}
                  >
                    {/* Map over displayablePersonas instead of availablePersonas */}
                    {displayablePersonas.map(p => (
                      <option key={p} value={p}>
                        {p === "General Schedule GS" ? "GS" : p}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  sx={{
                      backgroundColor: '#0D1B2A',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      textTransform: 'none',
                      '&:hover': {
                        backgroundColor: '#1B263B',
                      },
                      marginLeft: '10px',
                      height: '40px',
                  }}
                  onClick={handleSavePreferences}
                >
                  Confirm
                </Button>
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px' }}>
            <input 
                type="text" 
                value={userInput} 
                onChange={e => setUserInput(e.target.value)} 
                onKeyDown={handleKeyDown}
                placeholder="Type your message here..." 
                style={{ flexGrow: 1, padding: '8px', backgroundColor: '#0D1B2A', color: '#FFFFFF', border: '1px solid #1B263B', borderRadius: '4px',  outline: 'none', height: '40px', fontSize:'16px'}}
              />
              {isGenerating ? (
                <Button
                  sx={{
                    padding: '8px 16px',
                    backgroundColor: '#9c1f1f',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    '&:hover': {
                      backgroundColor: '#771717',
                    },
                  }}
                  onClick={handleStopGeneration}
                >
                  Stop
                </Button>
              ) : (
                <Button
                  sx={{
                    padding: '8px 16px',
                    backgroundColor: '#0D1B2A',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    '&:hover': {
                      backgroundColor: '#1B263B',
                    },
                  }}
                  onClick={handleSendMessage}
                >
                  Send
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* All Sources Container - use flex proportion */}
        {showSourcesDropdown && (
          <Box sx={{ 
            // Use flex proportion
            flex: '0 0 25%', // fixed proportion of the available space
            minWidth: { xs: '200px', sm: '250px' }, // Minimum width for usability
            maxWidth: '350px', // Maximum width to prevent excessive sizing
            border: '1px solid #1B263B',
            borderRadius: '8px',
            backgroundColor: '#121212',
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: '10px',
            boxSizing: 'border-box',
            boxShadow: '0 3px 6px rgba(0,0,0,0.3)',
            height: '100%',
            // Add transition for appearing
            animation: 'slideIn 0.3s ease-in-out',
            // Responsive font sizes
            '& h3': {
              fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' }
            },
            '& .source-question': {
              fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' }
            },
            '& .source-item': {
              fontSize: { xs: '0.75rem', sm: '0.8rem', md: '0.9rem' }
            }
          }}
          ref={sourcesDropdownRef}
          >
            <h3 style={{ margin: '0 0 10px 0', color: '#E0E1DD', textAlign: 'center' }}>All Sources</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Render sources by question */}
              {Object.entries(sourcesByQuestion).map(([questionNum, sources]) => (
                <div key={`question-${questionNum}`}>
                  {/* Question header */}
                  <div 
                    id={`question-${questionNum}`}
                    onClick={() => toggleQuestion(questionNum)}
                    className="source-question" // Add class for responsive styling
                    style={{ 
                      cursor: 'pointer',
                      border: '1px solid #1B263B',
                      borderRadius: '4px',
                      backgroundColor: '#0D1B2A',
                      color: '#FFFFFF',
                      padding: '8px 12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontWeight: 'bold',
                      userSelect: 'none',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <span>{getQuestionLabel(parseInt(questionNum))} ({sources.length})</span>
                    {expandedQuestions[questionNum] ? 
                      <ExpandLessIcon style={{ fontSize: '16px' }} /> : 
                      <ExpandMoreIcon style={{ fontSize: '16px' }} />
                    }
                  </div>
                  
                  {/* Sources for this question */}
                  {expandedQuestions[questionNum] && (
                    <div style={{ 
                      marginLeft: '12px',
                      marginTop: '4px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      {sources.map((source, index) => (
                        <div key={`${questionNum}-${index}`}>
                          {/* Source header */}
                          <div 
                            onClick={() => toggleIndividualSource(questionNum, index)}
                            className="source-item" // Add class for responsive styling
                            style={{ 
                              cursor: 'pointer',
                              border: '1px solid #1B263B',
                              borderRadius: '4px',
                              backgroundColor: '#1B263B',
                              color: '#FFFFFF',
                              padding: '8px 12px',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              userSelect: 'none',
                              transition: 'background-color 0.2s'
                            }}
                          >
                            <span>{source.title || `Document ${index + 1}`}</span>
                            {expandedIndividualSources[`${questionNum}-${index}`] ? 
                              <ExpandLessIcon style={{ fontSize: '16px' }} /> : 
                              <ExpandMoreIcon style={{ fontSize: '16px' }} />
                            }
                          </div>
                          
                          {/* Source content */}
                          {expandedIndividualSources[`${questionNum}-${index}`] && (
                            <div style={{ 
                              padding: '10px', 
                              backgroundColor: '#121212', 
                              color: '#E0E1DD',
                              borderBottomLeftRadius: '4px',
                              borderBottomRightRadius: '4px',
                              maxHeight: '200px',
                              overflowY: 'auto',
                              borderLeft: '1px solid #1B263B',
                              borderRight: '1px solid #1B263B',
                              borderBottom: '1px solid #1B263B'
                            }}>
                              <ReactMarkdown>{source.content}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div> 
          </Box>
        )}
      </div>

      {/* Add animation keyframes for the sources panel */}
      {/* Add this to the top of your component */}
      {/* const slideInAnimation = `
        @keyframes slideIn {
          from {
            transform: translateX(50px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `; */}

      {/* Add style element near the top of your return statement */}
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(50px);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
      
      {/* Snackbar for copy notification */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity="success"
          sx={{
            width: '100% !important',
            backgroundColor: 'white !important',
            color: 'black !important',
            fontWeight: 'bold !important',
            border: '1px solid #ddd !important',
            '& .MuiAlert-icon': {
              color: 'black !important'
            },
            '& .MuiAlert-message': {
              fontWeight: 'bold !important'
            }
          }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </AppTheme>
  );
}

export default ChatPage;
