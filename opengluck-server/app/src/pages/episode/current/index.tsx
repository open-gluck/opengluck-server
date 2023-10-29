import { useCurrentEpisodeData } from "@/features/api";

export default function CurrentGlucose() {
  const { data, isLoading, error } = useCurrentEpisodeData();
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    throw new Error(String(error));
  }
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
