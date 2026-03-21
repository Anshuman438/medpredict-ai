const Chat = require('../models/Chat');
const asyncHandler = require('../utils/asyncHandler');
const axios = require('axios');
const generateGeminiResponse = require('../services/geminiService');

/* ---------------------------
   Symptom Extraction Utility
---------------------------- */
const knownSymptoms = [
  "Fever",
  "Headache",
  "Fatigue",
  "Cough",
  "Chest Pain",
  "Shortness of Breath",
  "Nausea",
  "Dizziness",
  "Sore Throat",
  "Body Ache",
  "Blurred Vision",
  "Rapid Heartbeat",
  "Chills",
  "Loss of Appetite",
  "Insomnia"
];

const extractSymptomsFromText = (text) => {
  return knownSymptoms.filter(sym =>
    text.toLowerCase().includes(sym.toLowerCase())
  );
};

/* ---------------------------
   Send Message
---------------------------- */
const sendMessage = asyncHandler(async (req, res) => {
  const { text } = req.body;

  if (!text) {
    res.status(400);
    throw new Error('Message text required');
  }

  let chat = await Chat.findOne({ user: req.user._id });

  if (!chat) {
    chat = await Chat.create({
      user: req.user._id,
      messages: []
    });
  }

  // Save user message
  chat.messages.push({ sender: 'user', text });

  // Extract symptoms
  const symptoms = extractSymptomsFromText(text);

  let mlData = {
    condition: "General Inquiry",
    risk: "Unknown",
    confidence: "N/A"
  };

  // Call ML only if symptoms detected
  if (symptoms.length > 0) {
    try {
      const mlResponse = await axios.post(
        `${process.env.ML_SERVICE_URL}/predict`,
        { symptoms }
      );

      mlData = mlResponse.data;

    } catch (error) {
      console.error("🔥 ML SERVICE ERROR:", error.message);
    }
  }

  let aiResponseText = "";

  try {
    const geminiReply = await generateGeminiResponse(
      chat.messages,
      mlData
    );

    aiResponseText = geminiReply;

  } catch (error) {
    console.error("🔥 CHAT CONTROLLER ERROR:", error);

    aiResponseText = `
Based on current analysis:

Condition: ${mlData.condition}
Risk: ${mlData.risk}
Confidence: ${mlData.confidence}

Please consult a medical professional if symptoms persist.
`;
  }

  // Save AI message
  chat.messages.push({
    sender: 'ai',
    text: aiResponseText
  });

  await chat.save();

  res.status(201).json(chat);
});

/* ---------------------------
   Get Chat History
---------------------------- */
const getChatHistory = asyncHandler(async (req, res) => {
  const chat = await Chat.findOne({ user: req.user._id });

  if (!chat) {
    return res.json({ messages: [] });
  }

  res.json(chat);
});

module.exports = { sendMessage, getChatHistory };