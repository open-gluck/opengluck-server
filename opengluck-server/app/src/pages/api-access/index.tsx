import { useToken } from "@/components/EnsureLoggedIn";

export default function ApiAccess() {
  const token = useToken();

  return !token ? null : (
    <>
      <h2>API Access</h2>
      <p>
        To configure apps to connect to OpenGlück, you will need to provide them
        with the following information:
      </p>

      <dl>
        <dt>Host:</dt>
        <dd>
          <code>{window.location.host}</code>{" "}
          <button
            onClick={() => navigator.clipboard.writeText(window.location.host)}
          >
            Copy
          </button>
        </dd>

        <dt>Token:</dt>
        <dd>
          <code>{token}</code>{" "}
          <button onClick={() => navigator.clipboard.writeText(token)}>
            Copy
          </button>
        </dd>
      </dl>
    </>
  );
}
