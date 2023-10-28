import { useUserdataList } from "@/features/api";
import Link from "next/link";

export default function Userdata() {
  const { data, isLoading, error } = useUserdataList();
  return (
    <>
      <h1>UserData</h1>
      {error && <div className="error">{String(error)}</div>}
      {!isLoading &&
        data &&
        data.map((userdataInfo) => (
          <>
            <h2>{userdataInfo.name}</h2>
            <div>Type: {userdataInfo.type}</div>
            <Link href={`/userdata/${userdataInfo.name}/${userdataInfo.type}`}>
              View
            </Link>
          </>
        ))}
    </>
  );
}
