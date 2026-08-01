const express = require('express');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

// Attempt to load Google Gen AI SDK
let GoogleGenAI;
try {
  GoogleGenAI = require('@google/genai').GoogleGenAI;
} catch (e) {
  console.warn('Note: @google/genai package is not installed. Summarization will use local fallback.');
}

const app = express();
const PORT = process.env.PORT || 3000;
let liveStoryState = null;

app.use(express.json());

// Serve static files from the current folder (contains index.html)
app.use(express.static(__dirname));

// Load local locations
let locations = [];
try {
  const fileData = fs.readFileSync(path.join(__dirname, 'locations.json'), 'utf8');
  locations = JSON.parse(fileData);
} catch (err) {
  console.error('Error reading locations.json:', err);
  // Simple in-memory fallback
  locations = [
    {
      id: "1",
      city: "Taipei",
      city_zh: "台北",
      country: "Taiwan",
      country_zh: "台灣",
      longitude: 121.5654,
      latitude: 25.033,
      utcOffset: 8,
      story: "Waking up to the smell of fresh soy milk and youtiao in a bustling traditional market.",
      story_zh: "在熱鬧的傳統市場中，聞著新鮮豆漿和油條的香氣醒來。",
      greeting: "Zao An!"
    }
  ];
}

// Lazy initialization of Gemini Client
let ai = null;
function getGeminiClient() {
  if (!ai && GoogleGenAI) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (apiKey) {
      ai = new GoogleGenAI({ apiKey });
    } else {
      console.warn("GEMINI_API_KEY is not defined in environment variables. Using fallback summarizer.");
    }
  }
  return ai;
}

// Fallback logic
function getFallbackSummary(story, language) {
  if (language === "zh") {
    return story.length > 35 ? story.slice(0, 35) + "..." : story;
  } else {
    const words = story.split(/\s+/);
    return words.length > 15 ? words.slice(0, 15).join(" ") + "..." : story;
  }
}

// Resilient retry function with backoff for transient Gemini API errors (503, 429, etc.)
async function callGeminiWithRetry(client, options, maxRetries = 2, delayMs = 1200) {
  for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
    try {
      return await client.models.generateContent(options);
    } catch (err) {
      const isTransient = err?.status === "UNAVAILABLE" || 
                          err?.code === 503 || 
                          err?.status === "RESOURCE_EXHAUSTED" || 
                          err?.code === 429 ||
                          err?.message?.includes("experiencing high demand") || 
                          err?.message?.includes("temporary") ||
                          err?.message?.includes("UNAVAILABLE");
      
      if (isTransient && attempt <= maxRetries) {
        console.warn(`Gemini API temporary error (attempt ${attempt}/${maxRetries + 1}): ${err?.message || err}. Retrying in ${delayMs * attempt}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
        continue;
      }
      throw err;
    }
  }
}

// 1. API: Get Notion Data
app.get('/api/notion-data', (req, res) => {
  res.json(locations);
});

// 1b. API: Receive latest live story payload from DSI
app.post('/api/live-story', (req, res) => {
  const payload = req.body || {};

  if (!payload.city && !payload.story && !payload.fullContent) {
    return res.status(400).json({ error: 'Story payload is required' });
  }

  liveStoryState = {
    ...payload,
    updatedAt: new Date().toISOString()
  };

  res.json({ success: true, state: liveStoryState });
});

// 1c. API: Read latest live story payload
app.get('/api/live-story', (req, res) => {
  if (!liveStoryState) {
    return res.status(404).json({ error: 'No live story available' });
  }
  res.json(liveStoryState);
});

// 2. API: Summarize Story with Gemini
app.post('/api/summarize-story', async (req, res) => {
  const { story, language } = req.body;
  if (!story) {
    return res.status(400).json({ error: "Story is required" });
  }

  const client = getGeminiClient();
  if (!client) {
    return res.json({ summary: getFallbackSummary(story, language) });
  }

  try {
    const prompt = language === "zh"
      ? `請將以下關於城市的早晨故事，縮寫成 30 到 50 個字（繁體中文）的簡短精彩介紹，不要有任何多餘的前言或後記："${story}"`
      : `Summarize this city morning story in exactly 30 to 50 words: "${story}"`;

    const response = await callGeminiWithRetry(client, {
      model: "gemini-3.5-flash",
      contents: prompt,
    });

    const summary = response.text?.trim() || story;
    res.json({ summary });
  } catch (err) {
    console.warn("Gemini summarization error:", err.message || err);
    res.json({ summary: getFallbackSummary(story, language) });
  }
});

// Serve index.html as the primary entrypoint
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`==================================================`);
  console.log(`  Raspberry Pi Terminal Monitor server is active!`);
  console.log(`  Access locally at: http://localhost:${PORT}`);
  console.log(`==================================================`);
});
