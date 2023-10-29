import { useRouter } from "next/router";
import { useUserdataLrange } from "@/features/api";
export default function UserdataLrange() {
  const router = useRouter();
  const userdata = router.query.userdata as string;
  const { data, isLoading, error } = useUserdataLrange(userdata);
  return isLoading || !data ? null : error ? (
    <div className="error">{String(error)}</div>
  ) : (
    data.map((item) => (
      <>
        <pre>{JSON.stringify(item, null, 2)}</pre>
        <hr />
      </>
    ))
  );
}
