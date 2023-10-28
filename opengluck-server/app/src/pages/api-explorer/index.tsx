import { useCallback, useState } from "react";
import { serverUrl } from "@/features/api";
import { useToken } from "@/components/EnsureLoggedIn";

export default function ApiExplorer() {
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState(
    "/opengluck/instant-glucose/find?from=2023-01-01&to=2023-12-31"
  );
  const [paylaod, setPayload] = useState("");
  const [response, setResponse] = useState("");
  const [isError, setIsError] = useState(false);
  const token = useToken();
  const handleSend = useCallback(async () => {
    const res = await fetch(`${serverUrl}${path}`, {
      method,
      ...(paylaod ? { body: paylaod } : {}),
      headers: {
        authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      setIsError(true);
      setResponse(await res.text());
      return;
    }
    setIsError(false);
    const res2 = res.clone(); // clone if we want to try to read the body as text
    try {
      setResponse(JSON.stringify(await res.json(), undefined, 4));
    } catch (e) {
      setResponse(await res2.text());
    }
  }, [method, path, paylaod, token]);
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(response);
  }, [response]);
  return (
    <>
      <h1>API Explorer</h1>
      <p>
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="DELETE">DELETE</option>
        </select>
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          style={{ width: 300 }}
        />
      </p>
      Payload:
      <pre>
        <textarea
          cols={80}
          rows={10}
          style={{ fontFamily: "monospace" }}
          value={paylaod}
          onChange={(e) => setPayload(e.target.value)}
        />
      </pre>
      <button
        onClick={handleSend}
        disabled={method === "GET" && paylaod !== ""}
      >
        Send
      </button>
      <hr />
      {!response ? null : (
        <>
          <p>Response: </p>
          <p>
            <button onClick={handleCopy}>Copy</button>
          </p>
          <pre className={isError ? "error" : ""}>{response}</pre>
        </>
      )}
    </>
  );
}
