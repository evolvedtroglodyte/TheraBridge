// Quick test to verify OpenAI API key works
const fs = require('fs');
const path = require('path');

// Manually load .env.local
const envPath = path.join(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
const lines = envContent.split('\n');
lines.forEach(line => {
  const match = line.match(/^OPENAI_API_KEY=(.+)$/);
  if (match) {
    process.env.OPENAI_API_KEY = match[1];
  }
});

const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function testOpenAI() {
  console.log('Testing OpenAI API connection...');
  console.log('API Key exists:', !!process.env.OPENAI_API_KEY);
  console.log('Key prefix:', process.env.OPENAI_API_KEY?.slice(0, 15));

  try {
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: 'Say "test successful"' }],
      max_tokens: 10,
    });

    console.log('\n✅ OpenAI API works!');
    console.log('Response:', completion.choices[0].message.content);
  } catch (error) {
    console.log('\n❌ OpenAI API error:');
    console.log('Error name:', error.name);
    console.log('Error message:', error.message);
    console.log('Status:', error.status);
  }
}

testOpenAI();
