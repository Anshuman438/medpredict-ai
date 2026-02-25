const axios = require('axios');

const generateGeminiResponse = async (promptText) => {
  try {
    const response = await axios.post(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
      {
        contents: [
          {
            parts: [
              {
                text: promptText
              }
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
    console.error("🔥 GEMINI REST ERROR:", error.response?.data || error.message);
    return "AI service temporarily unavailable.";
  }
};

module.exports = generateGeminiResponse;