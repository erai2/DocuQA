
export function saveToIndexedDB(record) {
  const dbRequest = indexedDB.open("suriNotebook", 1);
  dbRequest.onupgradeneeded = function(e) {
    const db = e.target.result;
    if (!db.objectStoreNames.contains("records")) {
      db.createObjectStore("records", { keyPath: "id", autoIncrement: true });
    }
  };
  dbRequest.onsuccess = function(e) {
    const db = e.target.result;
    const tx = db.transaction("records", "readwrite");
    tx.objectStore("records").add(record);
  };
}
