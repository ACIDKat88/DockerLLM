import React, { useState } from 'react';
import Button from '@mui/material/Button';

const postFeedback = async (feedbackType, feedbackData, sessionToken) => {
  let endpoint = "";
  if (feedbackType === "positive") {
    endpoint = "http://localhost/api/feedback/positive";
  } else if (feedbackType === "neutral") {
    endpoint = "http://localhost/api/feedback/neutral";
  } else if (feedbackType === "negative") {
    endpoint = "http://localhost/api/feedback/negative";
  } else {
    console.error("Invalid feedback type:", feedbackType);
  }
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": sessionToken,
      },
      body: JSON.stringify(feedbackData),
    });
    if (!response.ok) {
      console.error("Feedback post error", await response.text());
    } else {
      console.log("Feedback posted successfully");
    }
  } catch (error) {
    console.error("Error posting feedback:", error);
  }
};

function FeedbackButtons({ sessionToken, interactionData }) {
  const [showFeedbackOptions, setShowFeedbackOptions] = useState(false);

  const handleFeedbackClick = (type) => {
    if (!interactionData) {
      console.warn("No interaction data available for feedback.");
      return;
    }

    const feedbackData = {
      question: interactionData.question,
      model: interactionData.model,
      temperature: interactionData.temperature,
      dataset: interactionData.dataset,
      answer: interactionData.answer,
      personality: interactionData.personality,
      sources: interactionData.sources,
      chat_id: interactionData.chat_id,
      title: interactionData.model,
      elapsed_time: interactionData.elapsed_time
    };

    postFeedback(type, feedbackData, sessionToken);
    setShowFeedbackOptions(false);
  };

  // Shared style properties matching the Model Selection button.
  const buttonSx = {
    marginRight: '5px',
    backgroundColor: '#0D1B2A',
    color: '#FFFFFF',
    fontWeight: 'bold',
    '&:hover': {backgroundColor: '#1B263B',},
  };

  // Use the same container style as your model selection buttons.
  const optionsContainerStyle = {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    gap: '10px',
    padding: '10px',
    border: '1px solid #ccc',
    marginLeft: '10px'
  };

  // Define specific button styles for each feedback type
  const positiveButtonSx = {
    ...buttonSx,
    backgroundColor: '#2E7D32', // Darker green for positive
    '&:hover': {backgroundColor: '#388E3C',},
  };

  const neutralButtonSx = {
    ...buttonSx,
    backgroundColor: '#E65100', // Amber/dark orange for neutral
    '&:hover': {backgroundColor: '#EF6C00',},
  };

  const negativeButtonSx = {
    ...buttonSx,
    backgroundColor: '#B71C1C', // Darker red for negative
    '&:hover': {backgroundColor: '#C62828',},
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <Button
        onClick={() => setShowFeedbackOptions(prev => !prev)}
        sx={buttonSx}
        disabled={!interactionData}
      >
        Feedback
      </Button>
      {showFeedbackOptions && (
        <div style={optionsContainerStyle}>
          <Button 
            onClick={() => handleFeedbackClick("positive")} 
            sx={positiveButtonSx} 
            disabled={!interactionData}
          >
            Positive
          </Button>
          <Button 
            onClick={() => handleFeedbackClick("neutral")} 
            sx={neutralButtonSx} 
            disabled={!interactionData}
          >
            Neutral
          </Button>
          <Button 
            onClick={() => handleFeedbackClick("negative")} 
            sx={negativeButtonSx} 
            disabled={!interactionData}
          >
            Negative
          </Button>
        </div>
      )}
    </div>
  );
}

export default FeedbackButtons;
