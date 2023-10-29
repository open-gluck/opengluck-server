import { createAccount } from "@/features/api";
import { useCallback, useState } from "react";

export default function CreateAccount() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const handleCreateAccount = useCallback(async () => {
    setCreating(true);
    await createAccount({ login: username, password });
    window.location.reload();
  }, [username, password]);
  const handleChangeLogin = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value),
    []
  );
  const handleChangePassword = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value),
    []
  );
  return (
    <>
      <h1>Create Account</h1>
      <p>It looks like there are no accounts on this OpenGlück account.</p>
      <p>Now is the time to create your first account.</p>
      <p>
        Do not forget the user/pass! you will need it later and there is no
        option to recover.
      </p>
      <form>
        <p>
          <div>
            <label htmlFor="username">Username:</label>
          </div>
          <input
            type="text"
            name="username"
            value={username}
            onChange={handleChangeLogin}
          />
        </p>
        <p>
          <div>
            <label htmlFor="password">Password:</label>
          </div>
          <input
            type="password"
            name="password"
            value={password}
            onChange={handleChangePassword}
          />
        </p>
        <button disabled={creating} onClick={handleCreateAccount}>
          Create Account
        </button>
      </form>
    </>
  );
}
