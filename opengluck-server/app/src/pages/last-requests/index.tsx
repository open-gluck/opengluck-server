import { useLastRequests } from "@/features/api";

export default function LastRequests() {
  const { data, isLoading, error } = useLastRequests();
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      {data.map((request) => (
        <>
          <h2>
            <code>
              {request.method} {request.path}
            </code>
          </h2>
          <pre>
            {request.headers}
            {request.body}
          </pre>
          <hr />
        </>
      ))}
    </>
  );
}
