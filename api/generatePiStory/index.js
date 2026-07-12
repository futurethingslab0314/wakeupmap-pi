import OpenAI from 'openai';

export default async function handler(req, res) {
    // 設置 CORS 標頭
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // 處理 OPTIONS 請求
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    // 只允許 POST 請求
    if (req.method !== 'POST') {
        res.setHeader('Allow', ['POST']);
        res.status(405).json({ error: `方法 ${req.method} 不被允許` });
        return;
    }

    try {
        const { city, country, countryCode } = req.body;

        if (!city || !country) {
            res.status(400).json({ error: '缺少必要參數' });
            return;
        }

        const openai = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY
        });

        // 生成問候語和語言信息
        const greetingPrompt = `你是一位語言專家。請根據以下地點：${city}, ${country}${countryCode ? ` (${countryCode})` : ''}，
提供當地最常用語言的「早安」問候語。

請以JSON格式回覆，包含：
{
  "greeting": "當地語言的早安問候語",
  "language": "語言名稱(中文)",
  "languageCode": "ISO語言代碼"
}

範例：
- 德國：{"greeting": "Guten Morgen!", "language": "德語", "languageCode": "de"}
- 日本：{"greeting": "おはようございます", "language": "日語", "languageCode": "ja"}
- 法國：{"greeting": "Bonjour!", "language": "法語", "languageCode": "fr"}
- 美國：{"greeting": "Good morning!", "language": "英語", "languageCode": "en"}

注意：只回覆JSON，不要其他文字`;

        const greetingResponse = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: greetingPrompt }],
            temperature: 0.7,
            max_tokens: 150
        });

        let greetingData;
        try {
            greetingData = JSON.parse(greetingResponse.choices[0].message.content.trim());
        } catch (parseError) {
            // 如果解析失敗，使用預設值
            const rawGreeting = greetingResponse.choices[0].message.content.trim();
            greetingData = {
                greeting: rawGreeting,
                language: "英語",
                languageCode: "en"
            };
        }

        const translationPrompt = `請把以下地名翻譯成標準繁體中文，僅回傳 JSON：
{
  "city_zh": "城市中文名",
  "country_zh": "國家中文名"
}

city: ${city}
country: ${country}
countryCode: ${countryCode || ''}`;

        const translationResponse = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [{ role: "user", content: translationPrompt }],
            temperature: 0,
            max_tokens: 120,
            response_format: { type: "json_object" }
        });

        let translationData = { city_zh: city, country_zh: country };
        try {
            translationData = JSON.parse(translationResponse.choices[0].message.content.trim());
        } catch (parseError) {
            translationData = { city_zh: city, country_zh: country };
        }

        const cityZh = translationData.city_zh || city;
        const countryZh = translationData.country_zh || country;

        // 生成英文故事
        const storyPromptEn = `Write a vivid but concise English wake-up story about ${city}, ${country}${countryCode ? ` (${countryCode})` : ''}.

Requirements:
1. Start with: "Today you wake up in ${city}, ${country}."
2. Mention one distinctive local detail, landmark, culture, food, landscape, or historical element.
3. Keep it grounded, sensory, and slightly poetic.
4. Keep it to 80-140 English words.
5. Do not include Chinese.
6. Do not include markdown or bullet points.`;

        const storyResponseEn = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: storyPromptEn }],
            temperature: 0.8,
            max_tokens: 250
        });

        const storyEn = storyResponseEn.choices[0].message.content.trim();

        // 生成中文故事
        const storyPromptZh = `請生成一段關於 ${city}, ${country}${countryCode ? ` (${countryCode})` : ''} 的繁體中文甦醒故事。

要求：
1. 開頭必須是：「今天的你在${countryZh}的${cityZh}醒來。」
2. 描述一件和這座城市或國家特色有關的事情。
3. 要有畫面感、真實感與一點詩意。
4. 長度控制在80到140字。
5. 不要加 markdown，不要條列，不要英文。`;

        const storyResponseZh = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: storyPromptZh }],
            temperature: 0.8,
            max_tokens: 250
        });

        const storyZh = storyResponseZh.choices[0].message.content.trim();

        res.status(200).json({
            greeting: greetingData.greeting,
            language: greetingData.language,
            languageCode: greetingData.languageCode,
            story: storyEn,
            story_zh: storyZh,
            chineseStory: storyZh,
            trivia: storyZh,
            city,
            country,
            city_zh: cityZh,
            country_zh: countryZh
        });

    } catch (error) {
        console.error('生成故事時發生錯誤:', error);
        res.status(500).json({ error: error.message });
    }
} 
