import { useHbA1c } from "@/features/api";
import Link from "next/link";

function formatHbA1c(hba1c: number | undefined | null): string {
  if (hba1c === undefined || hba1c === null) {
    return "";
  }
  return `${hba1c.toFixed(1)} %`;
}

export default function HbA1c() {
  const now: Date = new Date();
  const todayAtMidnight = now;
  todayAtMidnight.setHours(0, 0, 0, 0);

  const {
    data: dataToday,
    isLoading: isLoadingToday,
    error: errorToday,
  } = useHbA1c(todayAtMidnight, new Date(todayAtMidnight.getTime() + 86400e3));
  const {
    data: dataLast24Hours,
    isLoading: isLoadingLast24Hours,
    error: errorLast24Hours,
  } = useHbA1c(new Date(now.getTime() - 86400e3), now);
  const {
    data: dataLastWeek,
    isLoading: isLoadingLastWeek,
    error: errorLastWeek,
  } = useHbA1c(new Date(now.getTime() - 86400e3), now);
  const {
    data: dataLast30Days,
    isLoading: isLoadingLast30Days,
    error: errorLast30Days,
  } = useHbA1c(new Date(now.getTime() - 86400e3), now);
  const {
    data: dataLast90Days,
    isLoading: isLoadingLast90Days,
    error: errorLast90Days,
  } = useHbA1c(new Date(now.getTime() - 86400e3), now);
  const anyError =
    errorToday ||
    errorLast24Hours ||
    errorLastWeek ||
    errorLast30Days ||
    errorLast90Days;

  if (
    isLoadingToday ||
    !dataToday ||
    isLoadingLast24Hours ||
    !dataLast24Hours ||
    isLoadingLastWeek ||
    !dataLastWeek ||
    isLoadingLast30Days ||
    !dataLast30Days ||
    isLoadingLast90Days ||
    !dataLast90Days
  ) {
    return null;
  }
  if (anyError) {
    throw new Error(String(anyError));
  }
  return (
    <>
      <h2>HbA1c</h2>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Today</td>
            <td className="hba1c">{formatHbA1c(dataToday.hba1c)}</td>
          </tr>
          <tr>
            <td>Last 24 Hours</td>
            <td className="hba1c">{formatHbA1c(dataLast24Hours.hba1c)}</td>
          </tr>
          <tr>
            <td>Last Week</td>
            <td className="hba1c">{formatHbA1c(dataLastWeek.hba1c)}</td>
          </tr>
          <tr>
            <td>Last 30 Days</td>
            <td className="hba1c">{formatHbA1c(dataLast30Days.hba1c)}</td>
          </tr>
          <tr>
            <td>Last 90 Days</td>
            <td className="hba1c">{formatHbA1c(dataLast90Days.hba1c)}</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}
