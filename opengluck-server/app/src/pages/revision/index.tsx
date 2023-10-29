import { useGetRevision } from "@/features/api";

export default function Revision() {
  const { data, isLoading, error } = useGetRevision();
  return isLoading || !data ? null : error ? (
    <div className="error">{String(error)}</div>
  ) : (
    <>
      <h1>Revision Info</h1>
      <p>
        Number: <b>{data.revision}</b>
      </p>
      <p>
        Changed at: <b>{data.revision_changed_at}</b>
      </p>
    </>
  );
}
