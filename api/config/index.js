// Firebase Web SDK 配置端點
export default function handler(req, res) {
    // 設定 CORS 標頭
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ 
            error: `方法 ${req.method} 不被允許` 
        });
    }

    // 從環境變數獲取 Firebase Web SDK 配置
    const firebaseConfig = {
        apiKey: process.env.FIREBASE_WEB_API_KEY,
        authDomain: process.env.FIREBASE_AUTH_DOMAIN,
        projectId: process.env.FIREBASE_PROJECT_ID,
        storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
        messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
        appId: process.env.FIREBASE_APP_ID
    };

    // 檢查必要的配置是否存在
    const missingConfig = [];
    if (!firebaseConfig.apiKey) missingConfig.push('FIREBASE_WEB_API_KEY');
    if (!firebaseConfig.authDomain) missingConfig.push('FIREBASE_AUTH_DOMAIN');
    if (!firebaseConfig.projectId) missingConfig.push('FIREBASE_PROJECT_ID');
    if (!firebaseConfig.storageBucket) missingConfig.push('FIREBASE_STORAGE_BUCKET');
    if (!firebaseConfig.messagingSenderId) missingConfig.push('FIREBASE_MESSAGING_SENDER_ID');
    if (!firebaseConfig.appId) missingConfig.push('FIREBASE_APP_ID');

    if (missingConfig.length > 0) {
        console.error('❌ 缺少 Firebase Web SDK 配置:', missingConfig);
        return res.status(500).json({
            error: '缺少 Firebase Web SDK 配置',
            missingConfig: missingConfig
        });
    }

    console.log('✅ Firebase Web SDK 配置已載入');
    console.log('🔧 專案ID:', firebaseConfig.projectId);
    console.log('🔧 認證域名:', firebaseConfig.authDomain);

    // 設定全域變數並返回配置
    const configScript = `
        window.firebaseConfig = ${JSON.stringify(firebaseConfig)};
        console.log('🔥 Firebase 配置已載入:', window.firebaseConfig);
    `;

    res.setHeader('Content-Type', 'application/javascript');
    res.status(200).send(configScript);
}