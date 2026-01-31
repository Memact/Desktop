const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  console.log('[Electron] Creating main window...');
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    title: 'Memact',
    frame: false,
    center: true,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setIcon(path.join(__dirname, 'images/icon.png'));

  const startUrl = 'http://localhost:5173';
  mainWindow.loadURL(startUrl).catch(e => {
    console.error('[Electron] Error loading URL:', e);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(__dirname, 'engine', 'main.py');
    pythonProcess = spawn('python', [scriptPath, '--debug']);

    pythonProcess.on('spawn', () => {
      console.log('[Electron] Python backend process spawned successfully.');
      resolve();
    });

    pythonProcess.on('error', (err) => {
      console.error('[Electron] Failed to start Python backend.', err);
      reject(err);
    });

    pythonProcess.stdout.on('data', (data) => {
        const lines = data.toString().split('\n').filter(line => line.length > 0);
        lines.forEach(line => {
            try {
                const message = JSON.parse(line);
                if (message.type === 'debug') {
                    console.log(`[Python Debug] ${message.payload.message}`);
                    return;
                }
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.webContents.send('from-main', message);
                }
            } catch (error) {
                console.error(`[Python Raw Error] ${line}`);
            }
        });
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python Stderr] ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`[Python] Process exited with code ${code}`);
    });
  });
}

app.whenReady().then(async () => {
  console.log('[Electron] App is ready. Starting backend...');
  try {
    await startPythonBackend();
    console.log('[Electron] Backend started. Creating window...');
    createWindow();
  } catch (error) {
    console.error("Critical: Could not start Python backend. Application will exit.", error);
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

ipcMain.on('to-main', (event, arg) => {
  // Handle window controls
  if (arg.type === 'minimize-window') {
    if (mainWindow) mainWindow.minimize();
    return;
  }
  if (arg.type === 'maximize-window') {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
    return;
  }
  if (arg.type === 'close-window') {
    if (mainWindow) mainWindow.close();
    return;
  }

  // Forward other messages to Python
  if (pythonProcess && !pythonProcess.killed) {
    const message = JSON.stringify(arg) + '\n';
    pythonProcess.stdin.write(message);
  } else {
    console.warn('[Electron] Attempted to write to a killed Python process.');
  }
});
