require('dotenv').config();
const generateGeminiResponse = require('./services/geminiRestService');

async function test() {
  const result = await generateGeminiResponse(
    "Explain how AI works in a few words"
  );

  console.log(result);
}

test();