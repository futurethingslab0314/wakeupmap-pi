const NOTION_API_VERSION = '2022-06-28';
const NOTION_API_BASE = 'https://api.notion.com/v1';

function getText(value) {
    if (value === null || value === undefined) return '';
    return String(value).trim();
}

function readRichText(property) {
    return property?.rich_text?.map(part => part.plain_text || '').join('') || '';
}

function readTitle(property) {
    return property?.title?.map(part => part.plain_text || '').join('') || '';
}

function readDate(property) {
    return property?.date?.start || '';
}

function readNumber(property) {
    const value = property?.number;
    return Number.isFinite(value) ? value : null;
}

function mapPageToRecord(page) {
    const props = page.properties || {};
    return {
        pageId: page.id,
        userName: readTitle(props.userName),
        city: readRichText(props.city),
        country: readRichText(props.country),
        city_zh: readRichText(props.city_zh),
        country_zh: readRichText(props.country_zh),
        greeting: readRichText(props.greeting),
        story: readRichText(props.story),
        story_zh: readRichText(props.story_zh),
        recordedAtDate: readDate(props.recordedAtDate),
        recordedAt: readDate(props.recordedAt),
        localTime: readRichText(props.localTime),
        longtitude: readNumber(props.longtitude),
        latitude: readNumber(props.latitude)
    };
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
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'GET') {
        res.setHeader('Allow', ['GET']);
        res.status(405).json({ error: `Method ${req.method} not allowed` });
        return;
    }

    try {
        const databaseId = process.env.NOTION_DATABASE_ID;
        if (!databaseId) {
            res.status(500).json({ error: 'NOTION_DATABASE_ID is not configured' });
            return;
        }

        const { userName, date, limit = '100' } = req.query || {};
        const pageSize = Math.max(1, Math.min(parseInt(limit, 10) || 100, 100));

        const filter = [];
        if (userName) {
            filter.push({
                property: 'userName',
                title: {
                    equals: getText(userName)
                }
            });
        }
        if (date) {
            filter.push({
                property: 'recordedAtDate',
                date: {
                    equals: getText(date)
                }
            });
        }

        const payload = {
            page_size: pageSize,
            sorts: [
                {
                    property: 'recordedAt',
                    direction: 'ascending'
                }
            ]
        };

        if (filter.length === 1) {
            payload.filter = filter[0];
        } else if (filter.length > 1) {
            payload.filter = { and: filter };
        }

        const data = await notionRequest(`/databases/${databaseId}/query`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const records = (data.results || []).map(mapPageToRecord);
        const latest = records[records.length - 1] || null;

        res.status(200).json({
            success: true,
            records,
            latest
        });
    } catch (error) {
        console.error('Notion query failed:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to query Notion records',
            message: error.message
        });
    }
}
