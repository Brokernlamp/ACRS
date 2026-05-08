const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  getConfig: () => ipcRenderer.invoke("get-config"),
  checkInternet: () => ipcRenderer.invoke("check-internet"),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
  platform: process.platform,

  // License
  license: {
    activate: (key) => ipcRenderer.invoke("license:activate", key),
    status: () => ipcRenderer.invoke("license:status"),
    clear: () => ipcRenderer.invoke("license:clear"),
    getMachineId: () => ipcRenderer.invoke("license:get-machine-id"),
    getCredits: () => ipcRenderer.invoke("license:get-credits"),
    onCreditsUpdated: (cb) => ipcRenderer.on("credits:updated", (_, credits) => cb(credits)),
  },
});
