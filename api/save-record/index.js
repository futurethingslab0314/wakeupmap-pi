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

function buildNotionProperties(body) {
    const userName = getText(body.userName || body.userDisplayName || body.dataIdentifier || 'YuPie') || 'YuPie';
    const city = getText(body.city);
    const country = getText(body.country);
    const cityZh = getText(body.city_zh);
    const countryZh = getText(body.country_zh);
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

        const properties = buildNotionProperties(req.body || {});
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
