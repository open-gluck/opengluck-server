import { useRouter } from "next/router";
import { useUserdataZrange } from "@/features/api";
export default function UserdataZrange() {
  const router = useRouter();
  const userdata = router.query.userdata as string;
  const { data, isLoading, error } = useUserdataZrange(userdata);
  return isLoading || !data ? null : error ? (
    <div className="error">{String(error)}</div>
  ) : (
    data.map((item) => (
      <>
        <pre>{item}</pre>
        <hr />
      </>
    ))
  );
}
