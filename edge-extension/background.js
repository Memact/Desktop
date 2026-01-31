// This script runs in the background and listens for tab events.

const ENGINE_URL = 'http://localhost:8655/log';
let lastSentUrl = '';

// Function to send data to the Python engine
async function sendData(tab) {
  // Don't send data for empty, invalid, or internal pages
  if (!tab || !tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('edge://') || tab.url === 'about:blank') {
    return;
  }
  
  // Prevent sending the same URL repeatedly
  if (tab.url === lastSentUrl) {
    return;
  }

  lastSentUrl = tab.url;

  try {
    await fetch(ENGINE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        browser: 'Edge', // Hardcoded for this extension
        title: tab.title,
        url: tab.url
      }),
    });
  } catch (error) {
    // *** THIS IS THE CRUCIAL PART FOR DIAGNOSIS ***
    console.error("Memact Connector: Could not connect to the engine. Is it running? Is a firewall blocking it?");
  }
}

// Listen for when the active tab changes
chrome.tabs.onActivated.addListener(activeInfo => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (chrome.runtime.lastError) {
      // console.error(chrome.runtime.lastError.message);
    } else {
      sendData(tab);
    }
  });
});

// Listen for when a tab is updated (e.g., new URL, title change)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Send data if the tab is active and either the URL or title has changed
  if (tab.active && (changeInfo.url || changeInfo.title)) {
    sendData(tab);
  }
});
