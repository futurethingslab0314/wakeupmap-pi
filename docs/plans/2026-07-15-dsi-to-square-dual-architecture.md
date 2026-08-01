# DSI to Square Dual Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the original DSI UI with the `raspberrypi-square` interface while preserving the existing DSI behavior for story generation, Notion upload, location display, and audio playback.

**Architecture:** Keep `raspberrypi-dsi` as the hardware/control layer and let `raspberrypi-square` become the display layer. The Python side continues to own button handling, data collection, story/audio generation, and Notion persistence, while the square Node app serves the UI and receives ready-to-render story/location/audio state over a local API or injected browser events.

**Tech Stack:** Python 3, Selenium, OpenAI TTS, Node.js, Express, Leaflet, browser-injected JS, local HTTP endpoints.

---

### Task 1: Define the square-facing data contract

**Files:**
- Modify: `raspberrypi-dsi/main_web_dsi.py`
- Modify: `raspberrypi-dsi/web_controller_dsi.py`
- Modify: `raspberrypi-dsi/audio_manager.py`

**Step 1: Inspect the existing payload**

Verify which fields DSI already produces for a story event: city, city_zh, country, country_zh, latitude, longitude, countryCode, story, story_zh, fullContent, day, and user metadata.

**Step 2: Normalize the payload**

Add one canonical payload shape that can be sent to the frontend without the square UI needing to know DSI internals.

**Step 3: Keep backward compatibility**

Preserve the current DSI-only injection path so the original page still works if needed.

**Step 4: Verify locally**

Run: `python3 -m compileall raspberrypi-dsi`
Expected: no syntax errors.

### Task 2: Teach square to accept live DSI data

**Files:**
- Modify: `raspberrypi-square/server.js`
- Modify: `raspberrypi-square/index.html`

**Step 1: Add a live story endpoint**

Expose an endpoint that returns the latest DSI payload in the exact format the square UI needs.

**Step 2: Replace summary-only assumptions**

Update the square UI so it can render the full story payload directly, instead of only summarizing local `locations.json` content.

**Step 3: Support fallback data**

Keep `locations.json` as offline fallback so the UI still opens when DSI is unavailable.

**Step 4: Verify locally**

Run: `npm --prefix raspberrypi-square start`
Expected: server starts and UI loads.

### Task 3: Route Notion uploads through the DSI data flow

**Files:**
- Modify: `raspberrypi-dsi/audio_manager.py`
- Modify: `raspberrypi-dsi/main_web_dsi.py`
- Modify: `raspberrypi-square/server.js`

**Step 1: Confirm the write path**

Keep the Python side as the only component that creates the final story record destined for Notion.

**Step 2: Mirror to square**

After the Notion write succeeds, emit the same payload to square so the UI reflects the uploaded record immediately.

**Step 3: Handle failures safely**

If Notion upload fails, still surface the story in UI and log the failure clearly.

**Step 4: Verify locally**

Run: `python3 -m compileall raspberrypi-dsi`
Expected: no syntax errors.

### Task 4: Wire square to audio playback behavior

**Files:**
- Modify: `raspberrypi-dsi/audio_manager.py`
- Modify: `raspberrypi-square/index.html`

**Step 1: Define playback ownership**

Keep real TTS playback in DSI so the hardware path remains reliable.

**Step 2: Add UI audio cues**

Let square receive playback-state events so it can show "playing", "loading", and "ready" states alongside the story panel.

**Step 3: Keep browser sound effects**

Preserve the lightweight Web Audio hover/click cues in square.

**Step 4: Verify locally**

Run: `npm --prefix raspberrypi-square start`
Expected: browser UI opens and still responds to interaction cues.

### Task 5: Replace DSI startup with square entrypoint

**Files:**
- Modify: `raspberrypi-dsi/web_controller_dsi.py`
- Modify: `raspberrypi-dsi/main_web_dsi.py`
- Modify: `raspberrypi-square/server.js`

**Step 1: Point DSI at square**

Update the browser startup URL so DSI opens the square UI instead of the old DSI page.

**Step 2: Keep auto-fill behavior**

Ensure username, story trigger, and day navigation still happen automatically.

**Step 3: Confirm the DOM hooks**

Make sure square exposes the same or equivalent element IDs and JS entrypoints DSI expects.

**Step 4: Verify locally**

Run: `python3 -m compileall raspberrypi-dsi`
Expected: no syntax errors.

### Task 6: Validate end-to-end behavior

**Files:**
- Modify: `raspberrypi-square/index.html`
- Modify: `raspberrypi-square/server.js`
- Modify: `raspberrypi-dsi/main_web_dsi.py`

**Step 1: Test a cold start**

Start the square server, then start DSI, and verify the square UI loads with a live story.

**Step 2: Test a button action**

Trigger the DSI button flow and verify the same city, story, location, and audio behavior appears in the square UI.

**Step 3: Test fallback mode**

Run square without DSI and verify `locations.json` fallback still renders a usable UI.

**Step 4: Commit**

```bash
git add docs/plans/2026-07-15-dsi-to-square-dual-architecture.md
git commit -m "docs: add dsi to square implementation plan"
```
