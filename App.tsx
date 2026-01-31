
import React, { useState, useEffect } from 'react';
import './index.css';

const MicIcon = React.memo(() => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
    <line x1="12" y1="19" x2="12" y2="23"></line>
  </svg>
));

const MinimizeIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>;
const MaximizeIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>;
const CloseIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>;

const WindowControls = () => {
  const handleMinimize = () => window.electronAPI?.send('to-main', { type: 'minimize-window' });
  const handleMaximize = () => window.electronAPI?.send('to-main', { type: 'maximize-window' });
  const handleClose = () => window.electronAPI?.send('to-main', { type: 'close-window' });

  return (
    <div className="window-controls">
      <button onClick={handleMinimize} className="window-control-button"><MinimizeIcon /></button>
      <button onClick={handleMaximize} className="window-control-button"><MaximizeIcon /></button>
      <button onClick={handleClose} className="window-control-button close-button"><CloseIcon /></button>
    </div>
  );
};

const TitleBar = () => {
    return (
        <div className="title-bar">
            <WindowControls />
        </div>
    );
};

const LoadingIndicator = () => (
    <div className="loading-container">
        <div className="loader"></div>
        <img src="./images/icon.png" alt="Loading" className="loader-icon" />
    </div>
);

const App: React.FC = () => {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [screenshots, setScreenshots] = useState<string[]>([]);

  const getTimeline = () => {
    if (window.electronAPI) {
      window.electronAPI.send('to-main', { type: 'get_timeline' });
    }
  };

  const getScreenshots = () => {
    if (window.electronAPI) {
      window.electronAPI.send('to-main', { type: 'get_screenshots' });
    }
  };

  useEffect(() => {
    const handleFromMain = (data: { type: string; payload: any; }) => {
      switch (data.type) {
        case 'timeline_response':
          setTimeline(data.payload.timeline);
          setIsLoading(false);
          break;
        case 'screenshot_response':
          setScreenshots(data.payload.screenshots);
          break;
      }
    };

    if (window.electronAPI) {
      window.electronAPI.receive('from-main', handleFromMain);
      getTimeline();
    } else {
      console.warn('Electron API not found. Running in browser mode.');
      setIsLoading(false);
    }
  }, []);

  const handleMicClick = () => {
    if (window.electronAPI) {
      window.electronAPI.send('to-main', { type: 'transcribe_audio' });
    }
  };

  const handleExtractVisuals = (imagePath: string) => {
    if (window.electronAPI) {
      window.electronAPI.send('to-main', { type: 'extract_visuals', payload: { image_path: imagePath } });
    }
  };

  return (
    <div className="app-container">
      <TitleBar />
      <div className="header-content">
        <img src="./images/main.png" alt="Memact Logo" className="logo" />
        <button type="button" onClick={handleMicClick} className="window-control-button"><MicIcon /></button>
      </div>

      <div className="results-content">
        {isLoading ? (
          <LoadingIndicator />
        ) : (
          <>
            <pre className="results-text">{JSON.stringify(timeline, null, 2)}</pre>
            <button onClick={getScreenshots} className="extract-visuals-button">Show Screenshots</button>
            <div className="screenshots-container">
              {screenshots.map((screenshot, index) => (
                <div key={index} className="screenshot-item">
                  <img src={`http://localhost:8655/screenshots/${screenshot}`} alt={`screenshot-${index}`} className="screenshot-image" />
                  <button onClick={() => handleExtractVisuals(screenshot)} className="extract-visuals-button">Extract Visuals</button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default App;
