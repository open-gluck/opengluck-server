import { useRouter } from "next/router";
import { useUserdataString } from "@/features/api";
export default function UserdataString() {
  const router = useRouter();
  const userdata = router.query.userdata as string;
  const { data, isLoading, error } = useUserdataString(userdata);
  return isLoading ? null : error ? (
    <div className="error">{String(error)}</div>
  ) : (
    <pre>{data}</pre>
  );
}
