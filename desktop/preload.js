const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  getConfig: () => ipcRenderer.invoke("get-config"),
  checkInternet: () => ipcRenderer.invoke("check-internet"),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
  platform: process.platform,
});
