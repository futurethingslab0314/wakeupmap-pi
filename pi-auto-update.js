// The version in this document identifies the assets currently running.
(() => {
    const loadedVersion = document.querySelector('meta[name="pi-release"]')?.content;
    if (!loadedVersion || loadedVersion === 'local') return;

    const interval = 30_000;
    let idleSince = null;
    let checking = false;
    let reloading = false;

    function trackStandby() {
        const log = document.querySelector('#historyLogModal');
        const isIdle = document.querySelector('#waitingState.active')
            && !document.querySelector('#loadingState.active, #resultState.active, #errorState.active, #throatClearingPopup.show')
            && (!log || getComputedStyle(log).display === 'none');
        idleSince = isIdle ? idleSince ?? performance.now() : null;
    }

    function recordInteraction() {
        idleSince = null;
        trackStandby();
    }

    const observer = new MutationObserver(trackStandby);
    for (const id of ['waitingState', 'loadingState', 'resultState', 'errorState', 'historyLogModal', 'throatClearingPopup']) {
        const element = document.querySelector('#' + id);
        if (element) observer.observe(element, {attributes: true, attributeFilter: ['class', 'style']});
    }
    for (const event of ['pointerdown', 'pointerup', 'keydown', 'wheel']) {
        document.addEventListener(event, recordInteraction, {capture: true, passive: true});
    }
    trackStandby();

    setInterval(async () => {
        if (checking || reloading) return;
        checking = true;
        try {
            const response = await fetch('/pi-release.json', {
                cache: 'no-store',
                signal: AbortSignal.timeout(10_000),
            });
            if (!response.ok) return;

            const {version} = await response.json();
            trackStandby();
            if (typeof version === 'string' && version && version !== loadedVersion
                && idleSince !== null && performance.now() - idleSince >= interval) {
                reloading = true;
                window.location.reload();
            }
        } catch {
            // Keep the current screen usable during network or deployment outages.
        } finally {
            checking = false;
        }
    }, interval);
})();
