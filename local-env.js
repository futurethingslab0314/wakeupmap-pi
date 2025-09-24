// 本機環境變數注入（樹莓派可在部署時覆寫此檔案）
// 注意：此檔案會在 pi-script.js 之前載入
(function () {
  try {
    window.env = window.env || {};
    // 將 USER_NAME 設為樹莓派本機使用者名稱
    // 部署到樹莓派時請覆寫下行的值
    window.env.USER_NAME = '';
  } catch (e) {
    // 靜默失敗，避免中斷頁面載入
  }
})();


