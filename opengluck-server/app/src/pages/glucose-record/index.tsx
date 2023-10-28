import {
  useLastEpisodeRecords,
  GlucoseRecordType,
  useLastGlucoseRecords,
} from "@/features/api";
import Link from "next/link";

function LastGlucoseRecords({ type }: { type: GlucoseRecordType }) {
  const { data, isLoading, error } = useLastGlucoseRecords({
    type: GlucoseRecordType.scan,
  });
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      <h2>
        <pre>{type}</pre>
      </h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>mg/dL</th>
          </tr>
        </thead>
        <tbody>
          {data.map((record) => (
            <tr key={record.timestamp}>
              <td>{record.timestamp}</td>
              <td>{record.mgDl}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function GlucoseRecord() {
  const { data, isLoading, error } = useLastGlucoseRecords({
    type: GlucoseRecordType.scan,
  });
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      <h1>Glucose Records</h1>
      <LastGlucoseRecords type={GlucoseRecordType.scan} />
      <LastGlucoseRecords type={GlucoseRecordType.historic} />
    </>
  );
}
