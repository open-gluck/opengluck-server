import { useLastRecords } from "@/features/api";
import Link from "next/link";

export default function LastRecords() {
  const { data, isLoading, error } = useLastRecords();
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      <h2>Food Records</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Name</th>
            <th>Carbs</th>
            <th>Comps</th>
            <th>Record Until</th>
            <th>Remember Recording</th>
          </tr>
        </thead>
        <tbody>
          {data.food_records.map((record) => (
            <tr
              key={record.timestamp}
              className={record.deleted ? "deleted" : ""}
            >
              <td>{record.timestamp}</td>
              <td>{record.name}</td>
              <td>{record.carbs}</td>
              <td>{JSON.stringify(record.comps)}</td>
              <td>{record.record_until}</td>
              <td>
                <input
                  type="checkbox"
                  disabled
                  checked={record.remember_recording}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Instant Glucose Records</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>mg/dL</th>
            <th>Model Name</th>
            <th>Device ID</th>
          </tr>
        </thead>
        <tbody>
          {data.instant_glucose_records.map((record) => (
            <tr
              key={record.timestamp}
            >
              <td>{record.timestamp}</td>
              <td>{record.mgDl}</td>
              <td>{record.model_name}</td>
              <td>{record.device_id}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Glucose Records</h2>
      <table>
        <thead>
          <tr>
            <th>Record Class</th>
            <th>Timestamp</th>
            <th>Record Type</th>
            <th>mg/dL</th>
          </tr>
        </thead>
        <tbody>
          {data.glucose_records.map((record) => (
            <tr key={record.timestamp}>
              <td>Glucose</td>
              <td>{record.timestamp}</td>
              <td>{record.record_type}</td>
              <td>{record.mgDl}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Low Records</h2>
      <table>
        <thead>
          <tr>
            <th>Id</th>
            <th>Timestamp</th>
            <th>Sugar in Grams</th>
          </tr>
        </thead>
        <tbody>
          {data.low_records.map((record) => (
            <tr
              key={record.timestamp}
              className={record.deleted ? "deleted" : ""}
            >
              <td>{record.id}</td>
              <td>{record.timestamp}</td>
              <td>{record.sugar_in_grams}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Insulin Records</h2>
      <table>
        <thead>
          <tr>
            <th>Id</th>
            <th>Timestamp</th>
            <th>Units</th>
          </tr>
        </thead>
        <tbody>
          {data.insulin_records.map((record) => (
            <tr
              key={record.timestamp}
              className={record.deleted ? "deleted" : ""}
            >
              <td>{record.id}</td>
              <td>{record.timestamp}</td>
              <td>{record.units}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
