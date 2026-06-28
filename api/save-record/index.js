const NOTION_API_VERSION = '2022-06-28';
const NOTION_API_BASE = 'https://api.notion.com/v1';

function jsonResponse(res, status, payload) {
    res.status(status).json(payload);
}

function getText(value) {
    if (value === null || value === undefined) return '';
    return String(value).trim();
}

function getNumber(value) {
    const parsed = typeof value === 'number' ? value : parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function buildRichText(text) {
    const safeText = getText(text);
    if (!safeText) return [];
    return [{ type: 'text', text: { content: safeText } }];
}

function shouldTranslate(chineseValue, englishValue) {
    const zh = getText(chineseValue);
    const en = getText(englishValue);
    if (!en) return false;
    if (!zh) return true;
    return zh.toLowerCase() === en.toLowerCase();
}

async function translateLocationIfNeeded(body) {
    const city = getText(body.city);
    const country = getText(body.country);
    const countryCode = getText(body.countryCode || body.country_iso_code);

    if (!shouldTranslate(body.city_zh, city) && !shouldTranslate(body.country_zh, country)) {
        return {
            city_zh: getText(body.city_zh),
            country_zh: getText(body.country_zh)
        };
    }

    const openaiApiKey = process.env.OPENAI_API_KEY;
    if (!openaiApiKey) {
        return {
            city_zh: getText(body.city_zh) || city,
            country_zh: getText(body.country_zh) || country
        };
    }

    const prompt = [
        '請將以下地名翻譯為繁體中文。',
        '若原本已是中文請直接保留。',
        '請只回傳 JSON，格式為 {"city_zh":"","country_zh":""}。',
        `city: ${city || ''}`,
        `country: ${country || ''}`,
        `countryCode: ${countryCode || ''}`
    ].join('\n');

    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${openaiApiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'gpt-4o-mini',
                temperature: 0,
                response_format: { type: 'json_object' },
                messages: [
                    {
                        role: 'system',
                        content: '你是地名翻譯助手，請將城市與國家翻譯成標準繁體中文，僅回傳 JSON。'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(`OpenAI translation failed: ${response.status}`);
        }

        const data = await response.json();
        const rawContent = data?.choices?.[0]?.message?.content || '{}';
        const parsed = JSON.parse(rawContent);

        return {
            city_zh: getText(parsed.city_zh) || getText(body.city_zh) || city,
            country_zh: getText(parsed.country_zh) || getText(body.country_zh) || country
        };
    } catch (error) {
        console.warn('translateLocationIfNeeded failed:', error);
        return {
            city_zh: getText(body.city_zh) || city,
            country_zh: getText(body.country_zh) || country
        };
    }
}

async function buildNotionProperties(body) {
    const userName = getText(body.userName || body.userDisplayName || body.dataIdentifier || 'YuPie') || 'YuPie';
    const city = getText(body.city);
    const country = getText(body.country);
    const translatedLocation = await translateLocationIfNeeded(body);
    const cityZh = translatedLocation.city_zh;
    const countryZh = translatedLocation.country_zh;
    const greeting = getText(body.greeting);
    const story = getText(body.story);
    const storyZh = getText(body.story_zh) || story;
    const recordedAt = getText(body.recordedAt) || new Date().toISOString();
    const recordedAtDate = getText(body.recordedAtDate) || recordedAt.slice(0, 10);
    const localTime = getText(body.localTime);
    const longitude = getNumber(body.longtitude ?? body.longitude);
    const latitude = getNumber(body.latitude);

    const properties = {
        userName: {
            title: buildRichText(userName)
        },
        city: {
            rich_text: buildRichText(city)
        },
        city_zh: {
            rich_text: buildRichText(cityZh)
        },
        country: {
            rich_text: buildRichText(country)
        },
        country_zh: {
            rich_text: buildRichText(countryZh)
        },
        greeting: {
            rich_text: buildRichText(greeting)
        },
        story: {
            rich_text: buildRichText(story)
        },
        story_zh: {
            rich_text: buildRichText(storyZh)
        },
        recordedAtDate: {
            date: { start: recordedAtDate }
        },
        recordedAt: {
            date: { start: recordedAt }
        },
        localTime: {
            rich_text: buildRichText(localTime)
        }
    };

    if (longitude !== null) {
        properties.longtitude = { number: longitude };
    }

    if (latitude !== null) {
        properties.latitude = { number: latitude };
    }

    return properties;
}

async function notionRequest(path, options = {}) {
    const token = process.env.NOTION_INTEGRATION_TOKEN;
    if (!token) {
        throw new Error('NOTION_INTEGRATION_TOKEN is not configured');
    }

    const response = await fetch(`${NOTION_API_BASE}${path}`, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            'Notion-Version': NOTION_API_VERSION,
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const message = data?.message || `Notion API request failed with status ${response.status}`;
        throw new Error(message);
    }

    return data;
}

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'POST') {
        res.setHeader('Allow', ['POST']);
        jsonResponse(res, 405, { error: `Method ${req.method} not allowed` });
        return;
    }

    try {
        const databaseId = process.env.NOTION_DATABASE_ID;
        if (!databaseId) {
            jsonResponse(res, 500, { error: 'NOTION_DATABASE_ID is not configured' });
            return;
        }

        const properties = await buildNotionProperties(req.body || {});
        const page = await notionRequest('/pages', {
            method: 'POST',
            body: JSON.stringify({
                parent: { database_id: databaseId },
                properties
            })
        });

        jsonResponse(res, 200, {
            success: true,
            pageId: page.id,
            url: page.url
        });
    } catch (error) {
        console.error('Notion save-record failed:', error);
        jsonResponse(res, 500, {
            error: 'Failed to save record to Notion',
            message: error.message
        });
    }
}
