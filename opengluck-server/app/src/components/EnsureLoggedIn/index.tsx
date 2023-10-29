import { useDoWeHaveAnyAccounts } from "@/features/api";

import {
  useMemo,
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import CreateAccount from "../CreateAccount";
import LogIn from "../LogIn";

// create a context with the token of the current user
type UserContextType = {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
};

const dummyImpl = {
  token: null,
  setToken: () => {},
  logout: () => {},
};

export const UserContext = createContext<UserContextType>(dummyImpl);

export function useToken() {
  const { token } = useContext(UserContext);
  return token;
}

export function useLogout() {
  const { logout } = useContext(UserContext);
  return logout;
}

export default function EnsureLoggedInRoot({
  children,
}: {
  children: React.ReactElement;
}) {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    setToken(window.localStorage.getItem("token"));
  }, []);
  const handleSetToken = useCallback((token: string | null) => {
    setToken(token);
    if (token) {
      window.localStorage.setItem("token", token);
    } else {
      window.localStorage.removeItem("token");
    }
  }, []);
  const logout = useCallback(() => {
    handleSetToken(null);
    window.location.reload();
  }, [handleSetToken]);
  const context = useMemo(
    () => ({ token, setToken: handleSetToken, logout }),
    [token, handleSetToken, logout]
  );
  return (
    <UserContext.Provider value={context}>
      <EnsureLoggedIn>{children}</EnsureLoggedIn>
    </UserContext.Provider>
  );
}

export function EnsureLoggedIn({
  children,
}: {
  children: React.ReactElement;
}): React.ReactElement | null {
  const userContext = useContext(UserContext);
  const {
    isLoading: isLoadingAnyAccounts,
    data: doWeHaveAnyAccounts,
    error: anyAccountsError,
  } = useDoWeHaveAnyAccounts();
  if (!userContext.token) {
    if (isLoadingAnyAccounts) {
      return null;
    }
    if (anyAccountsError) {
      return <div>error {JSON.stringify(anyAccountsError)}</div>;
    }
    if (doWeHaveAnyAccounts) {
      return <LogIn />;
    } else {
      return <CreateAccount />;
    }
  }

  return children;
}
