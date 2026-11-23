// Firebase 配置端點已退場，保留檔案避免舊部署引用失敗
export default function handler(req, res) {
    res.status(410).json({
        error: 'Deprecated',
        message: 'Firebase configuration has been removed. Use Notion-based API instead.'
    });
}
