import { useCurrentData } from "@/features/api";

export default function CurrentData() {
  const { data, isLoading, error } = useCurrentData();
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
