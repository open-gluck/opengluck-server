import { useCallback, useMemo } from "react";
import {
  useLastInstantGlucoseRecords,
  useDownloadInstantGlucoseRecords,
  InstantGlucoseRecord,
} from "@/features/api";

function presentFileDownloadToUser(csv: string, filename: string) {
  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.setAttribute("hidden", "");
  a.setAttribute("href", url);
  a.setAttribute("download", filename);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function getTrend(data: [InstantGlucoseRecord], n: number): number | null {
  const record = data[n];
  const time = new Date(record.timestamp).getTime();
  for (var j = n + 1; j < data.length; j++) {
    const previousRecord = data[j];
    const previousTime = new Date(previousRecord.timestamp).getTime();
    if (time - previousTime > 10 * 60e3) {
      // calculate the average of mgDl around +/- 2 minutes of previousTime
      const previousMgDls = data.filter(
        ({ timestamp }) =>
          Math.abs(new Date(timestamp).getTime() - previousTime) < 2 * 60e3
      );
      const previousMgDl =
        previousMgDls.reduce((acc, { mgDl }) => acc + mgDl, 0) /
        previousMgDls.length;
      return (
        60.0 * ((record.mgDl - previousMgDl) / (time - previousTime)) * 60e3
      );
    }
  }
  return null;
}

function getTrendAsString(data: [InstantGlucoseRecord], n: number): string {
  const trend = getTrend(data, n);
  if (!trend) {
    return "";
  }
  if (trend.toLocaleString() === "0".toLocaleString()) {
    return "0";
  }
  return trend.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function getTrendDelta(
  trend: number | null,
  timestamp: Date | null,
  previousTrend: number | null,
  previousTimestamp: Date | null
): number | null {
  if (!trend || !previousTrend || !timestamp || !previousTimestamp) {
    return null;
  }
  const deltaValue = trend - previousTrend;
  if (!deltaValue) {
    return 0;
  }
  const deltaTime = timestamp.getTime() - previousTimestamp.getTime();
  const deltaByMinute = (deltaValue / deltaTime) * 60e3;
  return deltaByMinute;
}

function getTrendDeltaAsString(delta: number | null): string {
  if (delta === null) {
    return "";
  }
  if (delta.toLocaleString() === "0".toLocaleString()) {
    return "0";
  }
  return delta.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

export default function LastInstantGlucoseRecords() {
  const { data, isLoading, error } = useLastInstantGlucoseRecords();
  const downloadInstantGlucoseRecords = useDownloadInstantGlucoseRecords();
  const handleDownload = useCallback(async () => {
    const data = await downloadInstantGlucoseRecords();
    presentFileDownloadToUser(
      data,
      `last-instant-glucose-records-${Date.now()}.csv`
    );
  }, [downloadInstantGlucoseRecords]);

  const dataWithTrend = useMemo(
    () =>
      !data
        ? null
        : data.map((record, n) => ({
            ...record,
            trend: getTrend(data, n),
            trendAsString: getTrendAsString(data, n),
          })),
    [data]
  );
  const dataWithTrendAndDelta = useMemo(
    () =>
      !dataWithTrend
        ? null
        : dataWithTrend.map((record, n) => ({
            ...record,
            trendDelta:
              n + 1 >= dataWithTrend.length
                ? null
                : getTrendDelta(
                    record.trend,
                    new Date(record.timestamp),
                    dataWithTrend[n + 1].trend,
                    new Date(dataWithTrend[n + 1].timestamp)
                  ),
          })),
    [dataWithTrend]
  );

  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }

  return !dataWithTrendAndDelta ? null : (
    <>
      <button onClick={handleDownload}>Download</button>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Model Name</th>
            <th>Device ID</th>
            <th>mg/dL</th>
            <th>Trend (mg/dL/hr, last 10 minutes)</th>
            <th>∆Trend</th>
          </tr>
        </thead>
        <tbody>
          {dataWithTrendAndDelta.map((record) => (
            <tr key={record.timestamp}>
              <td>{record.timestamp}</td>
              <td>{record.model_name}</td>
              <td>{record.device_id}</td>
              <td>{record.mgDl}</td>
              <td>{record.trendAsString}</td>
              <td>{getTrendDeltaAsString(record.trendDelta)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
