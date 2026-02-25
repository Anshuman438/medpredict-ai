require('dotenv').config();
const axios = require('axios');

async function test() {
  try {
    const response = await axios.post(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
      {
        contents: [
          {
            parts: [
              {
                text: "Explain how AI works in a few words"
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

    console.log(response.data);

  } catch (error) {
    console.error("🔥 ERROR:", error.response?.data || error.message);
  }
}

test();