import { useCallback, useContext, useState } from "react";
import { UserContext } from "@/components/EnsureLoggedIn";

async function logIn(username: string, password: string): Promise<string> {
  // attempt to login on OpenGlück, and if successful return the token
  try {
    console.log(`Going to authorize login ${username}`);
    const res = await fetch(`/opengluck/login`, {
      method: "POST",
      body: JSON.stringify({
        login: username,
        password: password,
      }),
      headers: { "Content-Type": "application/json" },
    });
    const user = await res.json();

    // If no error and we have user data, return it
    if (!res.ok) {
      throw new Error("Login failed");
    }
    return user.token;
  } catch (e) {
    console.error("got error", e);
    throw e;
  }
}

export default function LogIn() {
  const userContext = useContext(UserContext);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loggingIn, setLoggingIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const handleLogIn = useCallback(async () => {
    setLoggingIn(true);
    try {
      const token = await logIn(username, password);
      userContext.setToken(token);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoggingIn(false);
    }
  }, [username, password, userContext]);
  return (
    <>
      <h1>Welcome Back!</h1>
      {error && <div className="error">{error}</div>}
      <form>
        <label htmlFor="email">Username</label>
        <input
          type="text"
          name="email"
          id="email"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <label htmlFor="password">Password</label>
        <input
          type="password"
          name="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p>
          <button type="submit" onClick={handleLogIn} disabled={loggingIn}>
            Log In
          </button>
        </p>
      </form>
    </>
  );
}
