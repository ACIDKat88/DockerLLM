import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import FeedbackButtons from '../components/shared-theme/feedbackbuttons.jsx';
import { getPersonas, logoutUser, getChatHistories, getUserPreferences, updateUserPreferences } from '../api.js'; // Import getPersonas, logoutUser, getChatHistories, and user preferences API functions
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import axios from 'axios';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import IconButton from '@mui/material/IconButton';

const availableModels = ["mistral:latest", "sskostyaev/mistral:7b-instruct-v0.2-q6_K-32k", "mistral:7b-instruct-v0.3-q3_K_M", "mistral-STRATGPT:latest"];

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
  
  // Debug messages state changes
  useEffect(() => {
    console.log("[DEBUG messages state] Messages updated:", messages.length, "messages");
    if (messages.length > 0) {
      console.log("[DEBUG messages state] First message:", messages[0]);
      console.log("[DEBUG messages state] Last message:", messages[messages.length - 1]);
    }
  }, [messages]);
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

  // Add state for tracking expanded sources (enhanced like ChatPage_Original)
  const [expandedSources, setExpandedSources] = useState(false);
  const [expandedMessageSources, setExpandedMessageSources] = useState({});
  const [expandedIndividualSources, setExpandedIndividualSources] = useState({});

  // Add state for tracking generation and abort controller
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingMessages, setStreamingMessages] = useState(new Set());
  const [abortControllers, setAbortControllers] = useState(new Map());

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

  // Add a state flag to prevent source recalculations during computation
  const [sourcesFinalized, setSourcesFinalized] = useState(false);
  const [isComputing, setIsComputing] = useState(false);

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

  // User ID state - will be updated when user info is fetched
  const [uid, setUid] = useState(localStorage.getItem("user_id"));

  async function fetchSources(query, dataset) {
    console.log("[DEBUG fetchSources] 🔍 Starting fetchSources with query:", query, "dataset:", dataset);
    try {
      console.log("[DEBUG fetchSources] 📡 Making API call to /api/sources");
      
      // Add timeout to detect hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.error("[DEBUG fetchSources] ⏰ API call timeout after 30 seconds");
        controller.abort();
      }, 30000);
      
      console.log("[DEBUG fetchSources] 📡 Sending request and waiting for response...");
      const response = await fetch("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/sources", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": sessionToken
        },
        body: JSON.stringify({ message: query, dataset }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId); // Clear timeout if request completes
      console.log("[DEBUG fetchSources] 📡 API response received! Status:", response.status, response.statusText);
      
      if (response.ok) {
        console.log("[DEBUG fetchSources] 📡 API call successful, parsing JSON...");
        const sourcesData = await response.json();
        console.log("[DEBUG fetchSources] 📡 JSON parsed successfully");
        console.log("[DEBUG fetchSources] 📋 Sources API returned data:", sourcesData);
        console.log("[DEBUG fetchSources] 📋 Data keys:", Object.keys(sourcesData || {}));
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
            
            // Force a UI refresh (don't interfere with aggressive refresh trigger)
            setForceUpdate(prev => prev < 100 ? prev + 1 : prev);
            
            // Also force the sources dropdown to update if it's open
            if (showSourcesDropdown) {
              setShowSourcesDropdown(false);
              setTimeout(() => setShowSourcesDropdown(true), 50);
            }
          }, 200);
        } else {
          console.log("No sources parsed from the content");
        }

        // Extract content for each source from the markdown content
        const extractSourceContent = (markdown, sourceName) => {
          if (!markdown || !sourceName) return 'No content available';
          
          // Split by source sections
          const sections = markdown.split('**Source');
          for (let section of sections) {
            if (section.includes(sourceName)) {
              // Extract the paragraph content
              const paragraphMatch = section.match(/\*\*Extracted Paragraph:\*\*\n\n(.*?)\n\n/s);
              if (paragraphMatch && paragraphMatch[1]) {
                return paragraphMatch[1].trim();
              }
            }
          }
          return 'No content available';
        };

        // Transform raw PDF elements into the expected format with title and content
        const formattedSources = rawSourcesForFeedback.map((element, index) => {
          // ENHANCED TITLE EXTRACTION: Try multiple sources for document titles
          let title = element.name || element.title;
          
          // If no direct title, try to extract from pdf_url path
          if (!title && element.pdf_url) {
            const urlParts = element.pdf_url.split('/');
            const fileName = urlParts[urlParts.length - 1];
            if (fileName && fileName !== '') {
              // Remove file extension and decode
              title = decodeURIComponent(fileName.replace(/\.pdf$/i, ''));
              console.log("[DEBUG] Extracted title from pdf_url:", title);
            }
          }
          
          // If still no title, try to extract from markdown content using better patterns
          if (!title && sourcesData.content) {
            const parsedFromMarkdown = parseSourcesMarkdown(sourcesData.content);
            if (parsedFromMarkdown[index] && parsedFromMarkdown[index].title) {
              title = parsedFromMarkdown[index].title;
              console.log("[DEBUG] Extracted title from markdown:", title);
            }
          }
          
          // Final fallback
          if (!title) {
            title = `Document ${index + 1}`;
            console.log("[DEBUG] Using fallback title:", title);
          }
          
          const content = extractSourceContent(sourcesData.content, title);
          
          return {
            title: title,
            content: content,
            pdf_url: element.pdf_url || ''
          };
        });
        
        console.log("[DEBUG] Formatted sources with enhanced title extraction:", formattedSources.map(s => ({ title: s.title, hasContent: !!s.content })));
        console.log("[DEBUG] Sample source content extraction:", formattedSources[0]?.content?.substring(0, 100) + "...");
        
        // Return the properly formatted source data
        console.log("[DEBUG fetchSources] 🎯 Returning formatted sources:", formattedSources.length, "sources");
        return formattedSources; 
      } else {
        const errorText = await response.text();
        console.error("[DEBUG fetchSources] ❌ API error:", response.status, errorText);
        return []; // Return empty array on error
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error("[DEBUG fetchSources] ❌ Sources API call was aborted (timeout):", error);
      } else {
        console.error("[DEBUG fetchSources] ❌ Exception in fetchSources:", error);
      }
      return []; // Return empty array on error
    }
  }
  
  
  
  // Fetch chat histories when component mounts
  useEffect(() => {
    console.log("[DEBUG useEffect] Component mounted, fetching chat histories...");
    console.log("[DEBUG useEffect] Session token exists:", !!sessionToken);
    // Only fetch chat histories once on initial load
    fetchChatHistories();
    
    // No polling interval setup or cleanup needed
  }, [sessionToken]);

  // Handle initial chat selection after both chat histories and hidden chats are loaded
  useEffect(() => {
    console.log("[DEBUG useEffect initial selection] Checking initial chat selection...");
    console.log("[DEBUG useEffect initial selection] chatHistories.length:", chatHistories.length);
    console.log("[DEBUG useEffect initial selection] selectedChat:", selectedChat);
    console.log("[DEBUG useEffect initial selection] hiddenChats.length:", hiddenChats.length);
    
    // Only run if we have chat histories, no chat selected, and hidden chats are loaded
    if (chatHistories.length > 0 && !selectedChat) {
      console.log("[DEBUG useEffect initial selection] 🔍 Looking for initial chat to load");
      
      const nonHiddenChats = chatHistories.filter(chat => !hiddenChats.includes(chat.id));
      console.log("[DEBUG useEffect initial selection] 📋 Non-hidden chats:", nonHiddenChats.map(h => h.id));
      
      let chatToLoad;
      if (nonHiddenChats.length > 0) {
        chatToLoad = nonHiddenChats[0].id;
        console.log("[DEBUG useEffect initial selection] ✅ Auto-selecting most recent non-hidden chat:", chatToLoad);
      } else {
        chatToLoad = chatHistories[0].id;
        console.log("[DEBUG useEffect initial selection] ⚠️ All chats are hidden, falling back to first chat:", chatToLoad);
      }
      
      // Load the selected chat
      loadChatMessages(chatToLoad);
    }
  }, [chatHistories, hiddenChats, selectedChat]); // Run when any of these change

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
      
      // Chat loading is now handled by separate useEffect
      console.log("[DEBUG fetchChatHistories] Found", sortedHistories.length, "chats");
      console.log("[DEBUG fetchChatHistories] Available chats:", sortedHistories.map(h => ({id: h.id, title: h.title})));
      console.log("[DEBUG fetchChatHistories] Initial chat selection will be handled by separate useEffect");
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
        console.log("[DEBUG loadChatMessages] Backend response data:", data);
        
        // Find the specific chat by ID
        const chatData = Object.entries(data).find(([id, _]) => id === chatId);
        console.log("[DEBUG loadChatMessages] Found chat data:", chatData);
        
        if (chatData && chatData.length > 1) {
          const [id, chatInfo] = chatData;
          console.log("[DEBUG loadChatMessages] Chat info:", chatInfo);
          console.log("[DEBUG loadChatMessages] Chat messages:", chatInfo.messages);
          
          // Process messages - simplified approach
          let processedMessages = [];
          let initialSourceStates = {};
          let tempSourcesByQuestion = {};
          let tempAllUniqueSources = [];
          
          if (Array.isArray(chatInfo.messages)) {
            console.log("[DEBUG loadChatMessages] Processing", chatInfo.messages.length, "messages");
            console.log("[DEBUG loadChatMessages] Raw messages from backend:", chatInfo.messages);
            
            let questionCounter = 0;
            
            // Process messages and build side panel data
            processedMessages = chatInfo.messages.map((msg, index) => {
              console.log(`[DEBUG loadChatMessages] 🔍 Processing message ${index}:`, msg);
              console.log(`[DEBUG loadChatMessages] 🔍 Message ${index} keys:`, Object.keys(msg));
              
              // Count user messages for question numbering
              if (msg.sender === 'user') {
                questionCounter++;
              }
              
              const normalizedMsg = {
                sender: msg.sender || 'bot', // Default to bot if not specified
                content: msg.content || msg.text || "",
                // Preserve any existing source information
                hasSources: msg.hasSources || false,
                sources: msg.sources || [],
                sourcesMarkdown: msg.sourcesMarkdown || ""
              };
              
              // If this message has sources, initialize expansion state AND populate side panel
              if (normalizedMsg.hasSources && normalizedMsg.sender === 'bot') {
                initialSourceStates[index] = false;
                console.log("[DEBUG loadChatMessages] 📋 Message", index, "has sources for question", questionCounter);
                console.log("[DEBUG loadChatMessages] 📄 sourcesMarkdown length:", normalizedMsg.sourcesMarkdown?.length || 0);
                console.log("[DEBUG loadChatMessages] 📑 sources type:", typeof normalizedMsg.sources);
                console.log("[DEBUG loadChatMessages] 📑 sources structure:", normalizedMsg.sources);
                
                // Parse sources for side panel
                let sourcesForSidePanel = [];
                
                // Handle array format sources
                if (Array.isArray(normalizedMsg.sources) && normalizedMsg.sources.length > 0) {
                  console.log("[DEBUG loadChatMessages] 📋 Processing sources in array format");
                  sourcesForSidePanel = normalizedMsg.sources.map(source => ({
                    title: source.name || source.title || 'Document',
                    content: source.content || 'No content available',
                    pdf_url: source.pdf_url || ''
                  }));
                } 
                // Handle object format sources: { content: "...", pdf_elements: [...] }
                else if (normalizedMsg.sources && typeof normalizedMsg.sources === 'object' && normalizedMsg.sources.pdf_elements && Array.isArray(normalizedMsg.sources.pdf_elements)) {
                  console.log("[DEBUG loadChatMessages] 📋 Processing sources in object format with pdf_elements");
                  sourcesForSidePanel = normalizedMsg.sources.pdf_elements.map((element, idx) => ({
                    title: element.name || element.title || `Document ${idx + 1}`,
                    content: element.content || 'No content available',
                    pdf_url: element.pdf_url || ''
                  }));
                } 
                // Fallback: parse from sourcesMarkdown
                else if (normalizedMsg.sourcesMarkdown) {
                  console.log("[DEBUG loadChatMessages] 📋 Parsing sources from sourcesMarkdown");
                  sourcesForSidePanel = parseSourcesMarkdown(normalizedMsg.sourcesMarkdown);
                }
                
                console.log("[DEBUG loadChatMessages] 📋 Final sourcesForSidePanel:", sourcesForSidePanel.length, "sources");
                
                // Add to side panel data structures
                if (sourcesForSidePanel.length > 0) {
                  console.log("[DEBUG loadChatMessages] 📋 Adding", sourcesForSidePanel.length, "sources to side panel for question", questionCounter);
                  
                  // Add to question-specific sources
                  if (!tempSourcesByQuestion[questionCounter]) {
                    tempSourcesByQuestion[questionCounter] = [];
                  }
                  tempSourcesByQuestion[questionCounter] = sourcesForSidePanel;
                  
                  // Add to all unique sources (avoiding duplicates)
                  const currentTitles = new Set(tempAllUniqueSources.map(s => s.title));
                  sourcesForSidePanel.forEach(source => {
                    if (!currentTitles.has(source.title)) {
                      tempAllUniqueSources.push(source);
                    }
                  });
                }
              }
              
              console.log("[DEBUG loadChatMessages] Processed message", index, ":", {
                sender: normalizedMsg.sender,
                contentLength: normalizedMsg.content?.length || 0,
                hasSources: normalizedMsg.hasSources
              });
              return normalizedMsg;
            });
          } else {
            console.log("[DEBUG loadChatMessages] No messages array found in chat info");
          }
          
          // Update the selected chat and its messages
          console.log("[DEBUG loadChatMessages] Setting messages:", processedMessages);
          setSelectedChat(chatId);
          setMessages(processedMessages);
          
          // **CRITICAL: Update side panel data structures**
          console.log("[DEBUG loadChatMessages] 📋 Setting side panel data:");
          console.log("[DEBUG loadChatMessages] 📋 sourcesByQuestion:", tempSourcesByQuestion);
          console.log("[DEBUG loadChatMessages] 📋 allUniqueSources count:", tempAllUniqueSources.length);
          
          setSourcesByQuestion(tempSourcesByQuestion);
          setAllUniqueSources(tempAllUniqueSources);
          
          // Update sources count
          const totalSources = Object.values(tempSourcesByQuestion).reduce((acc, sources) => acc + sources.length, 0);
          console.log("[DEBUG loadChatMessages] 📋 Total sources count calculated:", totalSources);
          console.log("[DEBUG loadChatMessages] 📋 Sources breakdown by question:", Object.keys(tempSourcesByQuestion).map(q => `Q${q}: ${tempSourcesByQuestion[q].length}`));
          setSourcesCount(totalSources);
          
          // DELAY SOURCES FINALIZATION: If we loaded existing sources, allow state updates to settle first
          if (totalSources > 0) {
            console.log("[DEBUG loadChatMessages] 🔒 Delaying finalization of", totalSources, "sources from loaded chat");
            setTimeout(() => {
              console.log("[DEBUG loadChatMessages] 🔒 Now finalizing sources from loaded chat");
              setSourcesFinalized(true);
            }, 300); // Shorter delay for loaded chats since no streaming involved
          }
          
          // Reset other source-related state
          setLastInteractionData(null);
          setSourceContent('');
          // Initialize expansion states for all messages with sources
          setExpandedMessageSources(initialSourceStates);
          
          // Initialize expansion states for side panel
          const initialExpandedQuestions = {};
          Object.keys(tempSourcesByQuestion).forEach(questionNum => {
            initialExpandedQuestions[questionNum] = false;
          });
          setExpandedQuestions(initialExpandedQuestions);
          
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
      // CRITICAL: Set the selected chat FIRST - this was missing!
      setSelectedChat(chatId);
      
      // Reset all sources-related state when switching chats
      setAllUniqueSources([]);
      setSourcesByQuestion({});
      setExpandedIndividualSources({});
      setExpandedMessageSources({});
      setExpandedQuestions({});
      setSourcesCount(0);
      setSourceContent('');
      setShowSourcesDropdown(false);
      
      // RESET SOURCES FINALIZATION: Allow recalculation for new chat
      console.log("[DEBUG handleSelectChat] 🔄 Resetting sources finalization for new chat");
      setSourcesFinalized(false);
      
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

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    const currentUserQuery = userInput;
    const messageId = `${Date.now()}-${Math.random()}`;  // Unique ID for this message
    
    setMessages(prev => [...prev, { sender: 'user', content: currentUserQuery }]);
    setUserInput('');
    
    // STREAMING NEVER BLOCKED: Don't set global isGenerating
    console.log("[DEBUG handleSendMessage] 🚀 Starting new streaming request - UI remains responsive");
    
    // RESET SOURCES FINALIZATION: Allow recalculation for new interaction
    console.log("[DEBUG handleSendMessage] 🔄 Resetting sources finalization for new interaction");
    setSourcesFinalized(false);

    // **CRITICAL: Ensure we have a chat selected - if not, select the top non-hidden chat**
    let currentChatId = selectedChat;
    if (!currentChatId && chatHistories.length > 0) {
      // Default to the first non-hidden chat in the list (most recent)
      console.log("[DEBUG handleSendMessage] 🔍 No chat selected, looking for non-hidden chat");
      console.log("[DEBUG handleSendMessage] 📋 Hidden chats:", hiddenChats);
      console.log("[DEBUG handleSendMessage] 📋 Available chats:", chatHistories.map(h => h.id));
      
      const nonHiddenChats = chatHistories.filter(chat => !hiddenChats.includes(chat.id));
      console.log("[DEBUG handleSendMessage] 📋 Non-hidden chats found:", nonHiddenChats.length);
      
      if (nonHiddenChats.length > 0) {
        currentChatId = nonHiddenChats[0].id;
        console.log("[DEBUG handleSendMessage] ✅ No chat selected, defaulting to top non-hidden chat:", currentChatId);
      } else {
        // Fallback to first chat if all are hidden
        currentChatId = chatHistories[0].id;
        console.log("[DEBUG handleSendMessage] ⚠️ No chat selected and all chats are hidden, defaulting to first chat:", currentChatId);
      }
      setSelectedChat(currentChatId);
      
      // Load the messages for this chat
      await loadChatMessages(currentChatId);
    } else if (!currentChatId && chatHistories.length === 0) {
      // If no chats exist at all, user must create one manually
      console.error("[ERROR] No chats available and none selected. User must create a new chat.");
      alert("Please create a new chat first by clicking the '+' button.");
      return; // Don't block UI, just return
    }

    const payload = {
      message: currentUserQuery,
      model: selectedModel,
      temperature: temperature,
      dataset: dataset,
      chat_id: currentChatId // Use the current chat ID
    };

    let botMessage = "";
    let messageIndex = null;
    let sourcesReceivedDuringStreaming = false; // Track if sources were received during streaming

    try {
      setMessages(prev => {
        messageIndex = prev.length;
        return [...prev, { sender: 'bot', content: "" }];
      });

      // Create unique abort controller for this request
      const abortController = new AbortController();
      setAbortControllers(prev => new Map(prev).set(messageId, abortController));
      
      // Track this message as streaming
      setStreamingMessages(prev => new Set(prev).add(messageId));
      console.log("[DEBUG handleSendMessage] 📡 Message streaming started:", messageId);

      const response = await fetch('https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': sessionToken,
        },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });

      if (!response.ok) {
        console.error("Error sending message:", response.statusText);
        setMessages(prev => {
          const updated = [...prev];
          if (updated[messageIndex]) {
            updated[messageIndex].content = `Error processing request: ${response.statusText}`;
          }
          return updated;
        });
        // Remove from streaming tracking
        setStreamingMessages(prev => {
          const newSet = new Set(prev);
          newSet.delete(messageId);
          return newSet;
        });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let partialLine = ""; // Accumulate partial lines
      let streamComplete = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log("[DEBUG] Stream ended by reader");
          break;
        }

        const chunk = decoder.decode(value);
        partialLine += chunk;

        // Process complete lines
        while (partialLine.includes('\n')) {
          const lineBreakIndex = partialLine.indexOf('\n');
          const currentLine = partialLine.slice(0, lineBreakIndex).trim();
          partialLine = partialLine.slice(lineBreakIndex + 1);

          if (!currentLine) continue;

          console.log("[DEBUG] Processing line:", currentLine);

          // Check for special end markers
          if (currentLine === "[DONE]" || currentLine === " [DONE]") {
            console.log("[DEBUG] 🏁 Stream complete marker received");
            streamComplete = true;
            break;
          }

          try {
            const parsed = JSON.parse(currentLine);
            if (parsed.sources) {
              sourcesReceivedDuringStreaming = true;
              
              // Handle both string and object formats for sources
              let sourcesData;
              if (typeof parsed.sources === 'string') {
                // Legacy string format
                sourcesData = parsed.sources.trim();
              } else if (typeof parsed.sources === 'object' && parsed.sources !== null) {
                // New object format with content and pdf_elements
                sourcesData = parsed.sources;
              }
              
              if (sourcesData) {
                setMessages(prev => {
                  const updated = [...prev];
                  if (updated[messageIndex]) {
                    // Set both sourcesMarkdown and sources for compatibility
                    if (typeof sourcesData === 'string') {
                      updated[messageIndex].sourcesMarkdown = sourcesData;
                    } else {
                      // For object format, use the content for markdown and the full object for sources
                      updated[messageIndex].sourcesMarkdown = sourcesData.content || '';
                      updated[messageIndex].sources = sourcesData; // Full object for getSourcesFromMessage
                    }
                    updated[messageIndex].hasSources = true;
                  }
                  return updated;
                });
              }
            }
            if (parsed.error) {
              console.error("[ERROR] Received error from stream:", parsed.error);
              setMessages(prev => {
                const updated = [...prev];
                if (updated[messageIndex]) {
                  updated[messageIndex].content += `\n\nError: ${parsed.error}`;
                }
                return updated;
              });
            } else if (parsed.token) {
              botMessage += parsed.token;
              setMessages(prev => {
                const updated = [...prev];
                if (updated[messageIndex]) {
                  updated[messageIndex].content = botMessage;
                }
                return updated;
              });
            }
          } catch (e) {
            console.log("[DEBUG] Non-JSON line, treating as text:", currentLine);
            botMessage += currentLine;
            setMessages(prev => {
              const updated = [...prev];
              if (updated[messageIndex]) {
                updated[messageIndex].content = botMessage;
              }
              return updated;
            });
          }
        }

        if (streamComplete) break;
      }

      console.log("[DEBUG] 📁 Stream processing complete for message:", messageId);
      
      // STREAMING NEVER BLOCKED: Remove from streaming tracking instead of setting global flag
      setStreamingMessages(prev => {
        const newSet = new Set(prev);
        newSet.delete(messageId);
        console.log("[DEBUG] 📁 Remaining streaming messages:", newSet.size);
        return newSet;
      });
      
      // Clean up abort controller
      setAbortControllers(prev => {
        const newMap = new Map(prev);
        newMap.delete(messageId);
        return newMap;
      });

      console.log("[DEBUG] 📁 Stream processing complete, checking for sources...");
      console.log("[DEBUG] 📁 Dataset:", dataset, "| Current query:", currentUserQuery);
      console.log("[DEBUG] 📁 About to set isGenerating to false");

      setIsGenerating(false); // Mark generation as complete after stream ends
      
      // DELAY SOURCES FINALIZATION: Allow all async state updates to complete first
      console.log("[DEBUG] 📁 Delaying sources finalization to allow state updates to complete");
      setTimeout(() => {
        console.log("[DEBUG] 📁 Now finalizing sources after state updates have settled");
        
        // TRIGGER AGGRESSIVE REFRESH: Use a flag to trigger refresh in useEffect with current messages state
        console.log("[DEBUG] 📁 🔄 TRIGGERING AGGRESSIVE REFRESH via state update");
        setForceUpdate(prev => prev + 100); // Large increment to trigger refresh
        
        // Delay finalization to allow the aggressive refresh to complete
        setTimeout(() => {
          setSourcesFinalized(true);
          console.log("[DEBUG] 📁 🔒 Sources finalized after aggressive refresh");
        }, 100); // Short delay to let the useEffect-based refresh complete
      }, 300); // Reduced delay since race condition is fixed - just need time for UI updates

      console.log("[DEBUG] 📁 Checking if sources were received during streaming...");
      // **SOURCES SHOULD ALREADY BE RECEIVED DURING STREAMING - NO SEPARATE FETCH NEEDED**
      
      console.log("[DEBUG] 📁 🎯 sourcesReceivedDuringStreaming flag:", sourcesReceivedDuringStreaming);
      console.log("[DEBUG] 📁 🎯 dataset:", dataset);
      console.log("[DEBUG] 📁 🎯 Should trigger fallback:", !sourcesReceivedDuringStreaming && dataset !== "None");
      
      if (!sourcesReceivedDuringStreaming && dataset !== "None") {
        // Fallback: only fetch sources separately if they weren't received during streaming
        console.log("[DEBUG] 📁 🚫 FALLBACK TRIGGERED - No sources received during streaming, calling fetchSources");
        console.log("[DEBUG] 📁 🚫 THIS SHOULD NOT HAPPEN IF STREAMING WORKED PROPERLY");
        try {
          console.log("[DEBUG] 🔍 Fetching sources after streaming...");
          console.log("[DEBUG] 🔍 Calling fetchSources with query:", currentUserQuery, "dataset:", dataset);
          const sources = await fetchSources(currentUserQuery, dataset);
          console.log("[DEBUG] 🔍 fetchSources returned:", sources);
          
          if (sources && sources.length > 0) {
            console.log("[DEBUG] ✅ Sources fetched successfully! Count:", sources.length);
            console.log("[DEBUG] ✅ Sample source:", sources[0]);
            
            // Convert fetchSources result to match older message format
            const pdf_elements = sources.map(source => ({
              name: source.title || 'Document',
              display: "side",
              pdf_url: source.pdf_url || '',
              content: source.content || 'No content available'
            }));
            
            // Create sourcesMarkdown as STRING (like ChatPage_Original.jsx working format)
            const sourcesMarkdownString = `**Relevant Sources and Extracted Paragraphs:**\n\n${sources.map((source, idx) => 
              `**Source:** **${source.title || source.name || 'Document'}**\n\n**Extracted Paragraph:**\n\n${source.content || 'No content available'}\n\nView full PDF: [Click Here](${source.pdf_url || ''})\n\n`
            ).join('')}`;
            
            console.log("[DEBUG] ✅ Generated sourcesMarkdown string with", pdf_elements.length, "pdf_elements");
            
            setMessages(prev => {
              const updated = [...prev];
              if (updated[messageIndex]) {
                updated[messageIndex].hasSources = true;
                updated[messageIndex].sources = pdf_elements; // ARRAY format for getSourcesFromMessage
                updated[messageIndex].sourcesMarkdown = sourcesMarkdownString; // STRING format like ChatPage_Original.jsx
              }
              return updated;
            });
            
            // **CRITICAL: Update side panel data structures immediately**
            console.log("[DEBUG] 📋 Updating side panel with sources:", sources.length);
            
            // Get the current question number (count of user messages)
            const questionNumber = messages.filter(msg => msg.sender === 'user').length;
            console.log("[DEBUG] 📋 Current question number:", questionNumber);
            
            // Update sourcesByQuestion for the side panel
            setSourcesByQuestion(prev => {
              const updated = { ...prev };
              if (!updated[questionNumber]) {
                updated[questionNumber] = [];
              }
              
              // Add the new sources, avoiding duplicates
              const currentTitles = new Set(updated[questionNumber].map(s => s.title));
              sources.forEach(source => {
                if (!currentTitles.has(source.title)) {
                  updated[questionNumber].push(source);
                }
              });
              
              console.log("[DEBUG] 📋 Updated sourcesByQuestion:", updated);
              return updated;
            });
            
            // Update allUniqueSources for the side panel dropdown
            setAllUniqueSources(prevSources => {
              // Create a Set with current titles for easy duplicate checking
              const currentSourceTitles = new Set(prevSources.map(source => source.title));
              
              // Filter out sources we already have
              const newSources = sources.filter(source => !currentSourceTitles.has(source.title));
              console.log("[DEBUG] 📋 Adding", newSources.length, "new unique sources to side panel");
              
              // Return updated array with new unique sources added
              return [...prevSources, ...newSources];
            });
            
            // Force update the sources count for the side panel button (finalization is delayed)
            setTimeout(() => {
              const total = calculateTotalSources();
              setSourcesCount(total);
              console.log("[DEBUG] 📋 Updated sources count:", total, "sourcesFinalized:", sourcesFinalized);
              
              // Force UI refresh (don't interfere with aggressive refresh trigger)
              setForceUpdate(prev => prev < 100 ? prev + 1 : prev);
            }, 250); // Longer delay to ensure all state cascades complete
            
            // Update lastInteractionData with sources for feedback buttons
            const newInteractionData = {
              question: currentUserQuery,
              answer: botMessage,
              sources: pdf_elements, // Use pdf_elements array for backend compatibility
              sourcesMarkdown: sourcesMarkdownString, // Use string format for backend compatibility
              model: selectedModel,
              temperature: temperature,
              dataset: dataset,
              personality: persona,
              chat_id: currentChatId, // Use the current chat ID
              elapsed_time: 0, // Not tracked in frontend
              messageIndex: messageIndex
            };
            console.log("[DEBUG] 🎯 Setting lastInteractionData with sources:", newInteractionData);
            setLastInteractionData(newInteractionData);
          } else {
            console.log("[DEBUG] ❌ No sources returned from fetchSources");
            // No sources, but still set interaction data for feedback
            const newInteractionDataNoSources = {
              question: currentUserQuery,
              answer: botMessage,
              sources: [], // Empty array for pdf_elements
              sourcesMarkdown: '', // Empty string for content
              model: selectedModel,
              temperature: temperature,
              dataset: dataset,
              personality: persona,
              chat_id: currentChatId, // Use the current chat ID
              elapsed_time: 0,
              messageIndex: messageIndex
            };
            console.log("[DEBUG] 🎯 Setting lastInteractionData without sources:", newInteractionDataNoSources);
            setLastInteractionData(newInteractionDataNoSources);
          }
        } catch (error) {
          console.error("[DEBUG] ❌ Error fetching sources:", error);
        }
      } else if (!sourcesReceivedDuringStreaming) {
        // No sources from stream and dataset is "None" or no sources available
        console.log("[DEBUG] 🚫 No sources received during streaming and dataset is 'None' or no sources available");
        const newInteractionDataNone = {
          question: currentUserQuery,
          answer: botMessage,
          sources: [],
          sourcesMarkdown: '',
          model: selectedModel,
          temperature: temperature,
          dataset: dataset,
          personality: persona,
          chat_id: currentChatId,
          elapsed_time: 0,
          messageIndex: messageIndex
        };
        console.log("[DEBUG] 🎯 Setting lastInteractionData without sources:", newInteractionDataNone);
        setLastInteractionData(newInteractionDataNone);
      } else {
        // Sources were already received during streaming - interaction data should already be set
        console.log("[DEBUG] ✅ Sources were received during streaming - skipping fallback fetch");
        console.log("[DEBUG] ✅ Streaming sources should have proper document titles");
      }

      // **CHAT HISTORY IS NOW SAVED IMMEDIATELY AFTER STREAMING IN BACKEND**
      // No need to save chat history here - it's handled automatically after streaming
      console.log("[DEBUG] ✅ Chat history is saved automatically by backend after streaming");
      console.log("[DEBUG] ✅ No separate save process needed in frontend");

    } catch (error) {
      console.error("[ERROR] Error in handleSendMessage:", error);
      if (error.name === 'AbortError') {
        console.log("[DEBUG] Request was aborted by user");
        setMessages(prev => {
          const updated = [...prev];
          if (updated[messageIndex]) {
            updated[messageIndex].content = "Request stopped by user.";
          }
          return updated;
        });
      } else {
        setMessages(prev => {
          const updated = [...prev];
          if (updated[messageIndex]) {
            updated[messageIndex].content = `Error: ${error.message}`;
          }
          return updated;
        });
      }
      
      // STREAMING NEVER BLOCKED: Remove from streaming tracking
      setStreamingMessages(prev => {
        const newSet = new Set(prev);
        newSet.delete(messageId);
        return newSet;
      });
      
      // Clean up abort controller
      setAbortControllers(prev => {
        const newMap = new Map(prev);
        newMap.delete(messageId);
        return newMap;
      });
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
    } else if (modelName === "mistral-STRATGPT:latest") {
      return "STRATGPT";
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
      
      console.log("Making API call to fetch user information...");
      
      // Use the correct /api/username endpoint that returns complete user info
      axios.get("https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/username", { headers })
        .then(response => {
          console.log("✅ User API response from /api/username:", response.data);
          
          if (response.data) {
            // Extract username
            if (response.data.username) {
              console.log("✅ Setting username:", response.data.username);
            setUsername(response.data.username);
            localStorage.setItem("username", response.data.username);
            }
            
            // **CRITICAL: Extract and store user_id**
            if (response.data.user_id) {
              console.log("✅ Setting user_id:", response.data.user_id);
              localStorage.setItem("user_id", response.data.user_id);
              setUid(response.data.user_id); // Update state for immediate use
            }
            
            // Store other useful info
            if (response.data.office_code) {
              localStorage.setItem("office_code", response.data.office_code);
            }
            
            console.log("✅ User information stored successfully");
          } else {
            console.error("❌ No user data received from /api/username");
          }
        })
        .catch(error => {
          console.error("❌ Error fetching user information from /api/username:", error);
          
          // If API call fails, try to use any existing stored values
          const storedUsername = localStorage.getItem("username");
          const storedUserId = localStorage.getItem("user_id");
          
                     if (storedUsername) {
             console.log("📱 Using stored username:", storedUsername);
             setUsername(storedUsername);
           } else if (storedUserId) {
             console.log("📱 Using stored user_id as fallback:", storedUserId);
             setUsername(storedUserId);
           } else {
             console.error("❌ No user information available - user may need to re-login");
          }
          
           // Update uid state if we have stored user_id
           if (storedUserId) {
             setUid(storedUserId);
          }
        });
    } else {
      console.warn("⚠️ No session token available - user may need to login");
      // Try to use any existing stored values as fallback
      const storedUsername = localStorage.getItem("username");
      const storedUserId = localStorage.getItem("user_id");
      
             if (storedUsername) {
         console.log("📱 Using stored username (no session):", storedUsername);
         setUsername(storedUsername);
       } else if (storedUserId) {
         console.log("📱 Using stored user_id (no session):", storedUserId);
         setUsername(storedUserId);
       }
       
       // Update uid state if we have stored user_id
       if (storedUserId) {
         setUid(storedUserId);
      }
    }
  }, [sessionToken]);

  // Function to extract direct source data from a bot message
  const getSourcesFromMessage = (message) => {
    // Log the entire message object to debug
    console.log("getSourcesFromMessage - Full message:", JSON.stringify(message, null, 2));
    
    // First check if message has direct sources attached (array format)
    if (message.sources && Array.isArray(message.sources)) {
      console.log("Using direct sources from message (array format):", message.sources);
      // Apply ENHANCED TITLE EXTRACTION to array format sources too
      const enhancedSources = message.sources.map((source, index) => {
        let title = source.name || source.title;
        
        // If no direct title, try to extract from pdf_url path
        if (!title && source.pdf_url) {
          const urlParts = source.pdf_url.split('/');
          const fileName = urlParts[urlParts.length - 1];
          if (fileName && fileName !== '') {
            title = decodeURIComponent(fileName.replace(/\.pdf$/i, ''));
          }
        }
        
        // If still no title, try to extract from content
        if (!title && source.content) {
          const docMatch = source.content.match(/Document:\s*([^\s]+\.pdf)/i);
          if (docMatch && docMatch[1]) {
            title = docMatch[1];
          }
        }
        
        // Final fallback - but ONLY if truly no title
        if (!title) {
          title = `Document ${index + 1}`;
        }
        // DON'T convert "Unknown Document" to generic - keep it as is
        
        return {
          title: title,
          content: source.content || 'No content available',
          pdf_url: source.pdf_url || ''
        };
      });
      console.log("Enhanced direct sources titles:", enhancedSources.map(s => `"${s.title}"`));
      return enhancedSources;
    }
    
    // Handle object format: { content: "...", pdf_elements: [...] }
    if (message.sources && typeof message.sources === 'object' && message.sources.pdf_elements && Array.isArray(message.sources.pdf_elements)) {
      console.log("Found sources in object format, extracting pdf_elements:", message.sources.pdf_elements);
      // Convert pdf_elements to the expected format using ENHANCED TITLE EXTRACTION
      const convertedSources = message.sources.pdf_elements.map((element, index) => {
        // ENHANCED TITLE EXTRACTION (same as streaming)
        let title = element.name || element.title;
        
        // If no direct title, try to extract from pdf_url path
        if (!title && element.pdf_url) {
          const urlParts = element.pdf_url.split('/');
          const fileName = urlParts[urlParts.length - 1];
          if (fileName && fileName !== '' && fileName !== 'undefined') {
            title = decodeURIComponent(fileName.replace(/\.pdf$/i, ''));
          }
        }
        
        // If still no title, try to extract from content
        if (!title && element.content) {
          const docMatch = element.content.match(/Document:\s*([^\s]+\.pdf)/i);
          if (docMatch && docMatch[1]) {
            title = docMatch[1];
          }
        }
        
        // Final fallback - but ONLY if truly no title
        if (!title) {
          title = `Document ${index + 1}`;
        }
        // DON'T convert "Unknown Document" to generic - keep it as is
        
        return {
          title: title,
          content: element.content || 'No content available',
          pdf_url: element.pdf_url || ''
        };
      });
      console.log("Converted sources from object format with enhanced titles:", convertedSources.map(s => `"${s.title}"`));
      return convertedSources;
    }
    
    // If we have hasSources flag but no sourcesMarkdown, return empty
    if (!message.sourcesMarkdown) {
      console.log("No sourcesMarkdown found in message");
      return [];
    }
    
    // Check if sourcesMarkdown is already a parsed object
    if (typeof message.sourcesMarkdown === 'object' && message.sourcesMarkdown !== null) {
      // If it has pdf_elements, use those with enhanced title extraction
      if (Array.isArray(message.sourcesMarkdown.pdf_elements)) {
        const sourceElements = message.sourcesMarkdown.pdf_elements.map((elem, index) => {
          // ENHANCED TITLE EXTRACTION (same as streaming)
          let title = elem.name || elem.title;
          
          // If no direct title, try to extract from pdf_url path
          if (!title && elem.pdf_url) {
            const urlParts = elem.pdf_url.split('/');
            const fileName = urlParts[urlParts.length - 1];
            if (fileName && fileName !== '' && fileName !== 'undefined') {
              title = decodeURIComponent(fileName.replace(/\.pdf$/i, ''));
            }
          }
          
          // If still no title, try to extract from content
          if (!title && elem.content) {
            const docMatch = elem.content.match(/Document:\s*([^\s]+\.pdf)/i);
            if (docMatch && docMatch[1]) {
              title = docMatch[1];
            }
          }
          
          // Final fallback - but ONLY if truly no title
          if (!title) {
            title = `Document ${index + 1}`;
          }
          // DON'T convert "Unknown Document" to generic - keep it as is
          
          return {
            title: title,
            content: elem.content || ''
          };
        });
        console.log("Extracted source elements from pdf_elements with enhanced titles:", sourceElements.map(s => `"${s.title}"`));
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
    
    // Force refresh source count whenever dropdown is toggled (only if not finalized)
    if (!sourcesFinalized) {
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
    } else {
      console.log("Sources are finalized, skipping recalculation on toggle");
    }
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
      return markdown.pdf_elements.map((elem, index) => ({
        title: elem.name || elem.title || `Document ${index + 1}`,
        content: elem.content || "No content available" 
      }));
    }
    
    // First, remove the header if present
    let cleanedMarkdown = markdown;
    if (cleanedMarkdown.includes('**Relevant Sources and Extracted Paragraphs:**')) {
      cleanedMarkdown = cleanedMarkdown.split('**Relevant Sources and Extracted Paragraphs:**')[1].trim();
    }
    
    // ENHANCED APPROACH: Look for the specific pattern: "**Source:** **Actual Title**"
    // This format is coming directly from the streaming response
    const sourceMatches = cleanedMarkdown.match(/\*\*Source:\*\*\s+\*\*([^*]+)\*\*/g);
    if (sourceMatches && sourceMatches.length > 0) {
      console.log("[DEBUG parseSourcesMarkdown] Found source titles in specific format:", sourceMatches.length);
      
      // Split the markdown into sections by the source pattern
      const sections = cleanedMarkdown.split(/\*\*Source:\*\*\s+\*\*[^*]+\*\*/);
      
      // Process each section, matching it with the corresponding source title
      const sources = [];
      sourceMatches.forEach((match, index) => {
        // Extract the title from the match pattern
        const titleMatch = match.match(/\*\*Source:\*\*\s+\*\*([^*]+)\*\*/);
        let title = `Document ${index + 1}`; // Better fallback
        
        if (titleMatch && titleMatch[1]) {
          title = titleMatch[1].trim();
          
          // ENHANCED TITLE CLEANING: Remove common prefixes and clean up
          title = title
            .replace(/^Source\s*\d*:?\s*/i, '') // Remove "Source 1:", "Source:", etc.
            .replace(/^Document\s*\d*:?\s*/i, '') // Remove "Document 1:", "Document:", etc.
            .replace(/\.pdf$/i, '') // Remove .pdf extension if present
            .trim();
          
          // If title becomes empty after cleaning, use fallback
          if (!title || title.length < 2) {
            title = `Document ${index + 1}`;
          }
          
          console.log("[DEBUG parseSourcesMarkdown] Cleaned title:", titleMatch[1], "→", title);
        }
        
        // Get the corresponding content section (skip the first section which appears before any source)
        let content = sections[index + 1] || "";
        
        // Extract text after "Extracted Paragraph:"
        if (content.includes('**Extracted Paragraph:**')) {
          content = content.split('**Extracted Paragraph:**')[1].trim();
        }
        
        // Clean up content by removing PDF links and extra whitespace
        if (content.includes('View full PDF:')) {
          content = content.split('View full PDF:')[0].trim();
        }
        
        // Skip if content is too short
        if (content.length >= 5) {
          sources.push({ title, content });
        }
      });
      
      console.log(`[DEBUG parseSourcesMarkdown] Parsed ${sources.length} sources with enhanced titles:`, 
                  sources.map(s => ({ title: s.title, contentLength: s.content.length })));
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
    console.log("[DEBUG] 🛑 Stopping current streaming requests");
    
    // Stop all current streaming requests
    abortControllers.forEach((controller, messageId) => {
      console.log("[DEBUG] 🛑 Aborting stream:", messageId);
      controller.abort();
    });
    
    // Clear all tracking
    setAbortControllers(new Map());
    setStreamingMessages(new Set());
    
    console.log("[DEBUG] 🛑 All streams stopped - UI remains responsive for new requests");
  };

  // Update the toggleSourcesDropdown function to work with our new flexbox layout
  const toggleSourcesDropdown = useCallback(() => {
    // If we're opening the dropdown, refresh all the source data first
    if (!showSourcesDropdown) {
      // RESPECT FINALIZED SOURCES: Skip refresh if sources are already finalized
      if (sourcesFinalized) {
        console.log("Sources are finalized, skipping refresh before showing dropdown");
        setShowSourcesDropdown(true);
        return;
      }
      
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
      
      // Force UI refresh (don't interfere with aggressive refresh trigger)
      setForceUpdate(prev => prev < 100 ? prev + 1 : prev);
      
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
  }, [messages, showSourcesDropdown, sourcesFinalized]);

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
    // RESPECT FINALIZED SOURCES: Only recalculate if sources are not finalized
    if (sourcesFinalized) {
      console.log("Sources are finalized, skipping recalculation");
      return;
    }
    
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
  }, [sourceContent, sourcesByQuestion, allUniqueSources, sourcesFinalized]);

  // Modify the calculateTotalSources function to be more thorough
  const calculateTotalSources = () => {
    let total = 0;
    
    console.log("[DEBUG calculateTotalSources] 🔢 Starting calculation...");
    console.log("[DEBUG calculateTotalSources] 📋 sourcesByQuestion:", sourcesByQuestion);
    console.log("[DEBUG calculateTotalSources] 📋 sourcesByQuestion keys:", Object.keys(sourcesByQuestion));
    
    // First, count sources from the sourcesByQuestion object
    Object.values(sourcesByQuestion).forEach((sourcesArray, index) => {
      if (Array.isArray(sourcesArray)) {
        console.log(`[DEBUG calculateTotalSources] 📄 Question ${index}: ${sourcesArray.length} sources`);
        total += sourcesArray.length;
      }
    });
    
    // Check all messages for any additional sources not tracked in sourcesByQuestion
    console.log(`[DEBUG calculateTotalSources] 📄 Checking ${messages.length} messages for additional sources`);
    messages.forEach((msg, msgIndex) => {
      if (msg.sender === 'bot' && (msg.hasSources || msg.sources)) {
        console.log(`[DEBUG calculateTotalSources] 📄 Checking bot message ${msgIndex}`);
        
        // Use getSourcesFromMessage to extract sources consistently
        const messageSources = getSourcesFromMessage(msg);
        
        if (messageSources && messageSources.length > 0) {
          console.log(`[DEBUG calculateTotalSources] 📄 Message ${msgIndex} has ${messageSources.length} sources`);
          
          // Only count sources that weren't already counted via sourcesByQuestion
          messageSources.forEach(source => {
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
                console.log(`[DEBUG calculateTotalSources] 📄 Adding uncounted source: "${source.title}"`);
                total += 1;
              }
            }
          });
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
    // RESPECT FINALIZED SOURCES: Skip recalculation if sources are finalized
    if (sourcesFinalized) {
      console.log("Sources are finalized, skipping bot message sources refresh");
      return;
    }
    
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
    // RESPECT FINALIZED SOURCES: Only calculate once during streaming, then preserve
    if (sourcesFinalized && sourcesCount > 0) {
      console.log("[DEBUG useEffect sourcesCount] 🔒 Sources are finalized with count:", sourcesCount, "- preserving state");
      return;
    }
    
    console.log("[DEBUG useEffect sourcesCount] 🔄 Sources data changed, recalculating...");
    console.log("[DEBUG useEffect sourcesCount] 📊 sourcesFinalized:", sourcesFinalized);
    console.log("[DEBUG useEffect sourcesCount] 📊 Messages count:", messages.length);
    console.log("[DEBUG useEffect sourcesCount] 📊 SourcesByQuestion keys:", Object.keys(sourcesByQuestion));
    console.log("[DEBUG useEffect sourcesCount] 📊 AllUniqueSources count:", allUniqueSources.length);
    
    // Update the sourcesCount state whenever sources change
    const total = calculateTotalSources();
    console.log("[DEBUG useEffect sourcesCount] 🎯 Calculated total:", total);
    
    // **ENHANCED ANTI-GLITCH PROTECTION**: Don't reset count incorrectly
    // This prevents the count from incorrectly dropping during streaming or incomplete data loading
    if (total > 0) {
      // Always update if we have a positive count
      console.log("[DEBUG useEffect sourcesCount] ✅ Setting sources count to:", total, "(positive count)");
      setSourcesCount(total);
    } else if (streamingMessages.size === 0 && (Object.keys(sourcesByQuestion).length === 0 || messages.length <= 1)) {
      console.log("[DEBUG useEffect sourcesCount] 🎯 No sources and no active streams - setting count to 0");
      setSourcesCount(0);
    } else {
      console.log("[DEBUG useEffect sourcesCount] ⚠️ Active streams:", streamingMessages.size, "sourcesByQuestion keys:", Object.keys(sourcesByQuestion), "messages:", messages.length);
    }
    
    // Force a re-render of the entire component to ensure all UI elements update
    // But don't interfere with aggressive refresh trigger (forceUpdate > 100)
    setTimeout(() => {
      setForceUpdate(prev => prev < 100 ? prev + 1 : prev);
    }, 100);
  }, [messages, sourceContent, sourcesByQuestion, allUniqueSources, forceUpdate, streamingMessages, sourcesFinalized, sourcesCount]);

  // AGGRESSIVE REFRESH: useEffect triggered after streaming to fix title display
  useEffect(() => {
    // Only trigger aggressive refresh when forceUpdate > 100 (streaming completion signal)
    if (forceUpdate > 100 && !sourcesFinalized && messages.length > 0) {
      console.log("[DEBUG useEffect AGGRESSIVE REFRESH] 🔄 TRIGGERED - Re-processing all messages with current state");
      console.log("[DEBUG useEffect AGGRESSIVE REFRESH] 📊 Current messages count:", messages.length);
      console.log("[DEBUG useEffect AGGRESSIVE REFRESH] 📊 Messages with sources:", messages.filter(m => m.sender === 'bot' && (m.hasSources || m.sources)).length);
      
      const tempSourcesByQuestion = {};
      const allMessageSources = [];
      let totalProcessedSources = 0;
      
      // Scan through all messages to collect sources with proper titles
      messages.forEach((msg, idx) => {
        if (msg.sender === 'bot' && (msg.hasSources || msg.sourcesMarkdown || (msg.sources && msg.sources.length > 0))) {
          // Find the corresponding user message index  
          const prevUserMsgs = messages.slice(0, idx).filter(m => m.sender === 'user').length;
          const questionNum = prevUserMsgs;
          
          console.log(`[DEBUG AGGRESSIVE REFRESH] 🔄 Processing bot message ${idx} for question ${questionNum}`);
          
          // Get sources using the SAME ENHANCED logic as streaming processing
          let sources = [];
          if (msg.sources && Array.isArray(msg.sources)) {
            sources = msg.sources.map((s, idx) => {
              // ENHANCED TITLE EXTRACTION (same as streaming)
              let title = s.name || s.title;
              
              // If no direct title, try to extract from pdf_url path
              if (!title && s.pdf_url) {
                const urlParts = s.pdf_url.split('/');
                const fileName = urlParts[urlParts.length - 1];
                if (fileName && fileName !== '' && fileName !== 'undefined') {
                  title = decodeURIComponent(fileName.replace(/\.pdf$/i, ''));
                }
              }
              
              // If still no title, try to extract from content
              if (!title && s.content) {
                const docMatch = s.content.match(/Document:\s*([^\s]+\.pdf)/i);
                if (docMatch && docMatch[1]) {
                  title = docMatch[1];
                }
              }
              
              // Final fallback - but ONLY if truly no title
              if (!title) {
                title = `Document ${idx + 1}`;
              }
              // DON'T convert "Unknown Document" to generic - keep it as is
              
              return {
                title: title,
                content: s.content || 'No content available',
                pdf_url: s.pdf_url || ''
              };
            });
          } else if (msg.sourcesMarkdown) {
            sources = parseSourcesMarkdown(msg.sourcesMarkdown);
          }
          
          console.log(`[DEBUG AGGRESSIVE REFRESH] 🔄 Found ${sources.length} sources for question ${questionNum}:`, sources.map(s => `"${s.title}"`));
          
          if (sources.length > 0) {
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
                  totalProcessedSources++;
                  console.log(`[DEBUG AGGRESSIVE REFRESH] 🔄 Added source: "${source.title}" to question ${questionNum}`);
                }
              }
            });
          }
        }
      });
      
      console.log("[DEBUG AGGRESSIVE REFRESH] 🔄 RESULTS:");
      console.log("[DEBUG AGGRESSIVE REFRESH] 🔄 Total sources processed:", totalProcessedSources);
      console.log("[DEBUG AGGRESSIVE REFRESH] 🔄 Questions with sources:", Object.keys(tempSourcesByQuestion));
      console.log("[DEBUG AGGRESSIVE REFRESH] 🔄 All source titles:", allMessageSources.map(s => `"${s.title}"`));
      
      // Force update all source-related state with refreshed data
      setSourcesByQuestion(tempSourcesByQuestion);
      setAllUniqueSources([...allMessageSources]); // Create new array to force update
      
      // Update sources count
      const totalSources = Object.values(tempSourcesByQuestion).reduce((acc, sources) => acc + sources.length, 0);
      setSourcesCount(totalSources);
      
      console.log("[DEBUG AGGRESSIVE REFRESH] 🔄 ✅ Updated all source state - titles should now display immediately");
    }
  }, [forceUpdate, sourcesFinalized, messages]);

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
                      backgroundColor: selectedChat === chat.id ? '#2E3E57' : '#0D1B2A', // Lighter shade for selected chat
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      textTransform: 'none',
                      width: '100%',
                      border: selectedChat === chat.id ? '2px solid #4A6A8A' : '2px solid transparent', // Add border for selected chat
                      '&:hover': {
                        backgroundColor: selectedChat === chat.id ? '#3A4F68' : '#1B263B',
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
                    
                    {/* Sources display for bot messages - ChatPage_Original.jsx structure */}
                    {msg.sender === 'bot' && (msg.hasSources || msg.sourcesMarkdown || (msg.sources && msg.sources.length > 0)) && (
                      <div style={{ marginTop: '10px', alignSelf: 'flex-start', maxWidth: '75%', position: 'relative', display: 'flex', alignItems: 'flex-start' }}>
                        {(() => {
                          const sources = getSourcesFromMessage(msg);
                          const sourceCount = sources.length;
                          
                          console.log(`Message ${index} sources:`, sources);
                          
                          if (sourceCount === 0) {
                            console.log("No sources found for message", index);
                            return null;
                          }
                          
                          // If only one source, use simplified view
                          if (sourceCount === 1) {
                            return (
                              <>
                                <div style={{ position: 'relative' }}>
                                  {/* Single source toggle */}
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

                                  {/* Copy button positioned absolutely to the right */}
                                  <div
                                    onClick={() => handleCopyMessage(msg.content)}
                                    style={{ 
                                      position: 'absolute',
                                      top: '0px',
                                      right: '-28px',
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
                                <div style={{ position: 'relative' }}>
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
                                                {/* Add PDF link if available */}
                                                {source.pdf_url && (
                                                  <div style={{ 
                                                    marginTop: '8px', 
                                                    paddingTop: '8px', 
                                                    borderTop: '1px solid #1B263B' 
                                                  }}>
                                                    <a 
                                                      href={source.pdf_url} 
                                                      target="_blank" 
                                                      rel="noopener noreferrer"
                                                      style={{ 
                                                        color: '#4A90E2', 
                                                        textDecoration: 'underline',
                                                        fontSize: '0.9rem'
                                                      }}
                                                    >
                                                      📄 View Full PDF
                                                    </a>
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {/* Copy button positioned absolutely to the right */}
                                  <div
                                    onClick={() => handleCopyMessage(msg.content)}
                                    style={{ 
                                      position: 'absolute',
                                      top: '0px',
                                      right: '-28px',
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
              <div style={{ display: 'flex', gap: '8px' }}>
                {/* STREAMING NEVER BLOCKED: Always allow new messages */}
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
                
                {/* Show stop button only if there are active streams */}
                {streamingMessages.size > 0 && (
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
                    Stop ({streamingMessages.size})
                  </Button>
                )}
              </div>
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
                              {/* Add PDF link if available */}
                              {source.pdf_url && (
                                <div style={{ 
                                  marginTop: '8px', 
                                  paddingTop: '8px', 
                                  borderTop: '1px solid #1B263B' 
                                }}>
                                  <a 
                                    href={source.pdf_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    style={{ 
                                      color: '#4A90E2', 
                                      textDecoration: 'underline',
                                      fontSize: '0.9rem'
                                    }}
                                  >
                                    📄 View Full PDF
                                  </a>
                                </div>
                              )}
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
