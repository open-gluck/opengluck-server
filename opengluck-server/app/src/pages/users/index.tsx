import { useToken } from "@/components/EnsureLoggedIn";
import {
  useCreateAdditionalAccount,
  useDeleteUser,
  useGetUsers,
} from "@/features/api";
import { useCallback, useState } from "react";

export default function Users() {
  const { data, isLoading, error, refetch } = useGetUsers();
  const token = useToken();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const createAdditionalAccount = useCreateAdditionalAccount();
  const handleCreateAccount = useCallback(async () => {
    setCreating(true);
    await createAdditionalAccount({ login: username, password });
    await refetch();
  }, [username, password, createAdditionalAccount, refetch]);
  const handleChangeLogin = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value),
    []
  );
  const handleChangePassword = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value),
    []
  );
  const deleteUser = useDeleteUser();
  const handleDeleteUser = useCallback(
    async (login: string) => {
      await deleteUser(login);
      await refetch();
    },
    [deleteUser, refetch]
  );
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return (
    <>
      <h2>List of Users</h2>
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((user) => (
            <tr key={user.login}>
              <td>{user.login}</td>
              <td>
                <button onClick={() => handleDeleteUser(user.login)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Create Additional User</h2>
      <form>
        <p>
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            name="username"
            value={username}
            onChange={handleChangeLogin}
          />
        </p>
        <p>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            name="password"
            value={password}
            onChange={handleChangePassword}
          />
        </p>
        <button disabled={creating} onClick={handleCreateAccount}>
          Create Additional User
        </button>
      </form>
      <h2>API Token</h2>
      <p>
        If you need to use a token to access the API, here is your current
        token:
      </p>
      <pre>{token}</pre>
    </>
  );
}
