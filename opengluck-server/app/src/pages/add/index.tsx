import { GlucoseRecordType, useUploadData } from "@/features/api";
import React, { useCallback, useState } from "react";

function genUuid(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    // eslint-disable-next-line no-bitwise
    const r = (Math.random() * 16) | 0;
    // eslint-disable-next-line no-bitwise
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function AddData() {
  const uploadData = useUploadData();
  const [insulinUnits, setInsulinUnits] = React.useState(0);
  const [insulinTimestamp, setInsulinTimestamp] = React.useState(new Date());
  const [insulinLog, setInsulinLog] = React.useState("");
  const [glucoseType, setGlucoseType] = React.useState("historic");
  const [glucoseMgDl, setGlucoseMgDl] = React.useState(100);
  const [glucoseTimestamp, setGlucoseTimestamp] = React.useState(new Date());
  const [glucoseLog, setGlucoseLog] = React.useState("Debug log");
  const handleSubmitInsulin = useCallback(async () => {
    setInsulinLog(`Submitting insulin ${insulinUnits} at ${insulinTimestamp}`);
    try {
      await uploadData({
        insulinRecords: [
          {
            id: genUuid(),
            units: insulinUnits,
            timestamp: insulinTimestamp.toISOString(),
            deleted: false,
          },
        ],
        glucoseRecords: [],
      });
      setInsulinLog(`Submitted insulin ${insulinUnits} at ${insulinTimestamp}`);
    } catch (e) {
      setInsulinLog(`Error submitting insulin: ${e}`);
    }
  }, [insulinUnits, insulinTimestamp, uploadData]);
  const handleSubmitGlucose = useCallback(async () => {
    setGlucoseLog(
      `Submitting glucose ${glucoseMgDl} of type ${glucoseType} at ${glucoseTimestamp}`
    );
    try {
      await uploadData({
        insulinRecords: [],
        glucoseRecords: [
          {
            record_type:
              glucoseType == "historic"
                ? GlucoseRecordType.historic
                : GlucoseRecordType.scan,
            timestamp: glucoseTimestamp.toISOString(),
            mgDl: glucoseMgDl,
          },
        ],
      });
      setGlucoseLog(
        `Submitted glucose ${glucoseMgDl} of type ${glucoseType} at ${glucoseTimestamp}`
      );
    } catch (e) {
      setGlucoseLog(`Error submitting glucose: ${e}`);
    }
  }, [glucoseMgDl, glucoseType, glucoseTimestamp, uploadData]);
  return (
    <>
      <h1>Add Insulin</h1>
      <form>
        Units:{" "}
        <input
          type="number"
          name="units"
          value={insulinUnits}
          onChange={(e) => setInsulinUnits(Number(e.target.value))}
        />
        Timestamp:{" "}
        <input
          type="datetime-local"
          name="timestamp"
          onChange={(e) => setInsulinTimestamp(new Date(e.target.value))}
          value={insulinTimestamp.toISOString().slice(0, 16)}
        />
        <p>
          <input
            type="button"
            value="Add Insulin"
            onClick={handleSubmitInsulin}
          />
        </p>
        <pre>{insulinLog}</pre>
      </form>
      <h1>Add Blood Glucose</h1>
      <form>
        Type:{" "}
        <select
          name="type"
          value={glucoseType}
          onChange={(e) => setGlucoseType(e.target.value)}
        >
          <option value="historic">Historic</option>
          <option value="scan">Scan</option>
        </select>
        Value:{" "}
        <input
          type="number"
          name="value"
          value={glucoseMgDl}
          onChange={(e) => setGlucoseMgDl(Number(e.target.value))}
        />
        Timestamp:{" "}
        <input
          type="datetime-local"
          name="timestamp"
          onChange={(e) => setGlucoseTimestamp(new Date(e.target.value))}
          value={glucoseTimestamp.toISOString().slice(0, 16)}
        />
        <p>
          <input
            type="button"
            value="Add Glucose"
            onClick={handleSubmitGlucose}
          />
        </p>
        <pre>{glucoseLog}</pre>
      </form>
    </>
  );
}
