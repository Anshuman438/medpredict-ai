const axios = require('axios');

const generateGeminiResponse = async (chatHistory, mlData) => {
  try {
    const formattedHistory = chatHistory
      .map(msg => `${msg.sender === "user" ? "User" : "AI"}: ${msg.text}`)
      .join("\n");

    const prompt = `
You are MedPredict AI, a professional and empathetic medical assistant.

Medical Context:
Condition: ${mlData.condition}
Risk: ${mlData.risk}
Confidence: ${mlData.confidence}

Conversation:
${formattedHistory}

Respond naturally, conversationally, and intelligently.
Do not sound robotic.
Do not claim medical diagnosis.
Encourage doctor consultation if serious.
`;

    const response = await axios.post(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
      {
        contents: [
          {
            parts: [
              { text: prompt }
            ]
          }
        ]
      },
      {
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": process.env.GEMINI_API_KEY
        }
      }
    );

    return response.data.candidates[0].content.parts[0].text;

  } catch (error) {
    console.error(" GEMINI REST ERROR:", error.response?.data || error.message);

    return `
Based on AI analysis:

Condition: ${mlData.condition}
Risk: ${mlData.risk}
Confidence: ${mlData.confidence}

Please monitor symptoms and consult a medical professional if necessary.
`;
  }
};

module.exports = generateGeminiResponse;