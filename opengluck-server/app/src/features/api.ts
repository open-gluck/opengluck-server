import { useQuery } from "react-query";
import { Webhook } from "@/features/webhooks";
import { useCallback } from "react";
import { useToken } from "@/components/EnsureLoggedIn";

export const serverUrl = "browser" in process ? "" : "http://localhost:8081";

export async function createAccount({
  login,
  password,
}: {
  login: string;
  password: string;
}) {
  await fetch(`${serverUrl}/opengluck/create-account`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      login,
      password,
    }),
  });
}

export function useDoWeHaveAnyAccounts() {
  const { data, isLoading, error } = useQuery<Boolean>("accounts", async () => {
    const res = await fetch(`${serverUrl}/opengluck/check-accounts`);
    if (!res.ok) {
      throw new Error("Failed to check if we have any accounts");
    }
    return res.json();
  });

  return { data, isLoading, error };
}

type LastRequest = {
  method: string;
  path: string;
  headers: string;
  body: string;
};

export function useLastRequests() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[LastRequest]>(
    "last-requests",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/last-requests`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get last requests");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

type User = {
  login: string;
};

export function useGetUsers() {
  const token = useToken();
  return useQuery<[User]>("users", async () => {
    const res = await fetch(`${serverUrl}/opengluck/users`, {
      headers: {
        authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      throw new Error("Failed to get users");
    }
    return res.json();
  });
}

export function useGetWebhooks(webhook: string) {
  const token = useToken();
  return useQuery<[Webhook]>(["webhook", webhook], async () => {
    const res = await fetch(`${serverUrl}/opengluck/webhooks/${webhook}`, {
      headers: {
        authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      throw new Error("Failed to get users");
    }
    return res.json();
  });
}

export function useDeleteUser() {
  const token = useToken();
  return useCallback(
    (login: string) => {
      return fetch(`${serverUrl}/opengluck/users/${login}`, {
        method: "DELETE",
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
    },
    [token]
  );
}
export function useCreateAdditionalAccount() {
  const token = useToken();
  return useCallback(
    async ({ login, password }: { login: string; password: string }) => {
      await fetch(`${serverUrl}/opengluck/create-account`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          login,
          password,
        }),
      });
    },
    [token]
  );
}

export function useCreateWebhook() {
  const token = useToken();
  return useCallback(
    async ({
      webhook,
      url,
      filter,
      includeLast,
    }: {
      webhook: string;
      url: string;
      filter: string;
      includeLast: boolean;
    }) => {
      await fetch(`${serverUrl}/opengluck/webhooks/${webhook}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          url,
          filter,
          include_last: includeLast,
        }),
      });
    },
    [token]
  );
}
export function useDeleteWebhook() {
  const token = useToken();
  return useCallback(
    ({ webhookId, id }: { webhookId: string; id: string }) => {
      return fetch(`${serverUrl}/opengluck/webhooks/${webhookId}/${id}`, {
        method: "DELETE",
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
    },
    [token]
  );
}

type LastWebhook = {
  date: Date;
  data: any;
};

export function useLastWebhooks(
  webhook: string,
  { filter }: { filter: string }
) {
  const token = useToken();
  return useQuery<[LastWebhook]>(
    ["last-webhooks", webhook, filter],
    async () => {
      const res = await fetch(
        `${serverUrl}/opengluck/webhooks/${webhook}/last?${new URLSearchParams({
          filter,
        })}`,
        {
          headers: {
            authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const json = await res.json();
      return json.map((x: any) => ({
        date: new Date(x.date),
        data: x.data,
      }));
    },
    { retry: false }
  );
}

export enum GlucoseRecordType {
  historic = "historic",
  scan = "scan",
}
type GlucoseRecord = {
  timestamp: string;
  record_type: GlucoseRecordType;
  mgDl: number;
};
type CurrentData = {
  current_glucose_record: GlucoseRecord | undefined;
  last_historic_glucose_record: GlucoseRecord | undefined;
  current_episode: Episode | undefined;
  current_episode_timestamp: string | undefined;
  has_cgm_real_time_data: boolean;
  revision: number;
};

type LowRecord = {
  id: string;
  timestamp: string;
  sugar_in_grams: number;
  deleted: boolean;
};

type InsulinRecord = {
  id: string;
  timestamp: string;
  units: number;
  deleted: boolean;
};

enum GlucoseSpeed {
  auto = "auto",
  custom = "custom",
  fast = "fast",
  medium = "medium",
  slow = "slow",
}

type PossibleCompressorsValue = {
  glucose_speed: GlucoseSpeed;
  comp: number | undefined;
};

type FoodRecord = {
  id: string;
  timestamp: string;
  deleted: boolean;
  name: string;
  carbs: number | undefined;
  comps: PossibleCompressorsValue;
  record_until: string | undefined;
  remember_recording: boolean;
};

type LastData = {
  glucose_records: GlucoseRecord[];
  instant_glucose_records: InstantGlucoseRecord[];
  low_records: LowRecord[];
  insulin_records: InsulinRecord[];
  food_records: FoodRecord[];
  revision: number;
};

export function useLastRecords() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<LastData>("last", async () => {
    const res = await fetch(`${serverUrl}/opengluck/last`, {
      headers: {
        authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      throw new Error("Failed to get last data");
    }
    const j = await res.json();
    return {
      revision: j["revision"],
      glucose_records: j["glucose-records"] ?? [],
      instant_glucose_records: j["instant-glucose-records"] ?? [],
      low_records: j["low-records"] ?? [],
      insulin_records: j["insulin-records"] ?? [],
      food_records: j["food-records"] ?? [],
    };
  });
  return { data, isLoading, error };
}

export function useLastGlucoseRecords({ type }: { type: GlucoseRecordType }) {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[GlucoseRecord]>(
    "last-glucose-records",
    async () => {
      const res = await fetch(
        `${serverUrl}/opengluck/glucose/last?${new URLSearchParams({
          type,
        })}`,
        {
          headers: {
            authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        throw new Error("Failed to get last data");
      }
      return await res.json();
    }
  );
  return { data, isLoading, error };
}

export function useCurrentData() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<CurrentData>(
    "current-data",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/current`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get current data");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

type UserdataInfoType = "string" | "list";
type UserdataInfo = {
  name: string;
  type: UserdataInfoType;
};

export function useUserdataList() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[UserdataInfo]>(
    "userdata",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/userdata`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get a list of userdata");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

export function useUserdataString(userdata: String) {
  const token = useToken();
  const { data, isLoading, error } = useQuery<String>(
    ["userdata-string", userdata],
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/userdata/${userdata}`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get a list of userdata");
      }
      return res.text();
    }
  );
  return { data, isLoading, error };
}

export function useUserdataLrange(userdata: String) {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[any]>(
    ["userdata-lrange", userdata],
    async () => {
      const res = await fetch(
        `${serverUrl}/opengluck/userdata/${userdata}/lrange`,
        {
          headers: {
            authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        throw new Error("Failed to get a list of userdata");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

export function useUserdataZrange(userdata: String) {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[string]>(
    ["userdata-zrange", userdata],
    async () => {
      const res = await fetch(
        `${serverUrl}/opengluck/userdata/${userdata}/zrange`,
        {
          headers: {
            authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        throw new Error("Failed to get a zrange of userdata");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

enum Episode {
  Unknown = "unknown",
  Disconnected = "disconnected",
  Low = "low",
  Normal = "normal",
  High = "high",
}

type EpisodeRecord = {
  timestamp: string;
  episode: Episode;
};

export function useCurrentEpisodeData() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<EpisodeRecord>(
    "current-episode-data",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/episode/current`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get current episode data");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

export function useLastEpisodeRecords() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[EpisodeRecord]>(
    "last-episode-records",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/episode/last`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get last episode data");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

type RevisionInfo = {
  revision: number | undefined;
  revision_changed_at: string | undefined;
};

export function useGetRevision() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<RevisionInfo>(
    "get-revision",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/revision`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get current revision info");
      }
      return res.json();
    }
  );
  return { data, isLoading, error };
}

export type InstantGlucoseRecord = {
  timestamp: string;
  mgDl: number;
  model_name: string;
  device_id: string;
};

export function useLastInstantGlucoseRecords() {
  const token = useToken();
  const { data, isLoading, error } = useQuery<[InstantGlucoseRecord]>(
    "last-instant-glucose-records",
    async () => {
      const res = await fetch(`${serverUrl}/opengluck/instant-glucose/last`, {
        headers: {
          authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to get last instant glucose data");
      }
      return await res.json();
    }
  );
  return { data, isLoading, error };
}

export function useDownloadInstantGlucoseRecords() {
  const token = useToken();
  return useCallback(async () => {
    const res = await fetch(`${serverUrl}/opengluck/instant-glucose/download`, {
      headers: {
        authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      throw new Error("Failed to download instant glucose record");
    }
    return await res.text();
  }, [token]);
}

export enum ExportType {
  JSON = "json",
  Swift = "swift",
}

export function useExportData() {
  const token = useToken();
  return useCallback(
    async ({ from, to, type }: { from: Date; to: Date; type: ExportType }) => {
      const res = await fetch(`${serverUrl}/opengluck/export`, {
        headers: {
          authorization: `Bearer ${token}`,
          "content-type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({
          from: from.toISOString(),
          to: to.toISOString(),
          type,
        }),
      });
      if (!res.ok) {
        throw new Error(`Failed to export data: ${await res.text()}`);
      }
      return await res.blob();
    },
    [token]
  );
}

export function useUploadData() {
  const token = useToken();
  return useCallback(
    async ({
      insulinRecords,
      glucoseRecords,
    }: {
      insulinRecords: InsulinRecord[];
      glucoseRecords: GlucoseRecord[];
    }) => {
      const res = await fetch(`${serverUrl}/opengluck/upload`, {
        headers: {
          authorization: `Bearer ${token}`,
          "content-type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({
          "insulin-records": insulinRecords,
          "glucose-records": glucoseRecords,
        }),
      });
      if (!res.ok) {
        throw new Error(`Failed to upload data: ${await res.text()}`);
      }
    },
    [token]
  );
}

type HbA1cData = {
  hba1c?: number;
};

export function useHbA1c(from: Date, to: Date) {
  const token = useToken();
  const { data, isLoading, error } = useQuery<HbA1cData>(
    `hbA&c from ${from.toISOString()} to ${to.toISOString()}`,
    async () => {
      const res = await fetch(
        `${serverUrl}/opengluck/hba1c?${new URLSearchParams({
          from: from.toISOString(),
          to: to.toISOString(),
        })}`,
        {
          headers: {
            authorization: `Bearer ${token}`,
            "content-type": "application/json",
          },
          method: "POST",
        }
      );
      if (!res.ok) {
        throw new Error(`Failed to get HbA1c: ${await res.text()}`);
      }
      const json = await res.json();
      console.log(
        `HbA1c from ${from.toISOString()} to ${to.toISOString()}`,
        json
      );
      return json;
    }
  );
  return { data, isLoading, error };
}
