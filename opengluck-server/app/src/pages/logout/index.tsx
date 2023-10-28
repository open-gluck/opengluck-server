import { useEffect } from "react";
import { useLogout } from "@/components/EnsureLoggedIn";

export default function Logout() {
  const logout = useLogout();
  useEffect(() => {
    logout();
  }, [logout]);
  return null;
}
