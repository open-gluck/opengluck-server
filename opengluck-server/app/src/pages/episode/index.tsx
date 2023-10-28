import { useLastEpisodeRecords } from "@/features/api";
import Link from "next/link";

export default function Episode() {
  const { data, isLoading, error } = useLastEpisodeRecords();
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      <Link href="/episode/current">View Only Current Episode</Link>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Episode</th>
          </tr>
        </thead>
        <tbody>
          {data.map((record) => (
            <tr key={record.timestamp}>
              <td>{record.timestamp}</td>
              <td>{record.episode}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
