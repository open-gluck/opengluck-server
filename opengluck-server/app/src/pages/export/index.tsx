import React, { useState, useCallback } from "react";
import { useExportData, ExportType } from "@/features/api";

// convert a date to a string in the format YYYY-MM-DD HH:MM, in local time
function convertDateToLocal(date: Date): string {
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60 * 1000);
  return localDate.toISOString().slice(0, 16);
}

export default function ExportData() {
  const [dateFrom, setDateFrom] = useState(
    new Date(Date.now() - 86400e3 * 1.5).toISOString()
  );
  const [dateTo, setDateTo] = useState(new Date(Date.now()).toISOString());
  const [exportType, setExportType] = useState("swift");
  const [data, setData] = useState("");
  const exportData = useExportData();

  const handleExport = useCallback(async () => {
    try {
      const blob = await exportData({
        from: new Date(dateFrom),
        to: new Date(dateTo),
        type: exportType as ExportType,
      });
      if (blob.type === "application/json") {
        setData(JSON.stringify(JSON.parse(await blob.text()), null, 2));
      } else {
        setData(await blob.text());
      }
    } catch (e) {
      setData(String(e));
    }
  }, [exportData, dateFrom, dateTo, exportType]);

  return (
    <>
      <h1>Export Data</h1>
      <p>
        Type:
        <select
          value={exportType}
          onChange={(e) => setExportType(e.target.value)}
        >
          <option value="json">JSON</option>
          <option value="swift">Swift</option>
        </select>
      </p>
      <p>
        From:{" "}
        <input
          type="datetime-local"
          value={convertDateToLocal(new Date(dateFrom))}
          onChange={(e) => setDateFrom(new Date(e.target.value).toISOString())}
        />
      </p>
      <p>
        To:{" "}
        <input
          type="datetime-local"
          value={convertDateToLocal(new Date(dateTo))}
          onChange={(e) => setDateTo(new Date(e.target.value).toISOString())}
        />
      </p>
      <p>
        <button onClick={handleExport}>Export</button>
      </p>
      <p>
        {!data ? null : (
          <textarea
            value={data}
            readOnly={true}
            style={{ width: "100%", height: "400px", fontFamily: "monospace" }}
          />
        )}
      </p>
    </>
  );
}
