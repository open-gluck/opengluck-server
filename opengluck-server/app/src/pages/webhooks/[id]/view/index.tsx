import { useLastWebhooks } from "@/features/api";
import { webhookTypes } from "@/features/webhooks";
import { useRouter } from "next/router";
import { useState } from "react";

export default function ViewWebhooks() {
  const router = useRouter();
  const webhookId = router.query.id as string;
  const webhookType = webhookTypes.find(
    (webhookType) => webhookType.id === webhookId
  );
  const [filter, setFilter] = useState("");
  const { data, isLoading, error } = useLastWebhooks(webhookId, { filter });

  if (!webhookType) {
    return <div>Webhook not found</div>;
  }
  return (
    <>
      <h1>Last {webhookType.name} Webhooks</h1>
      <label htmlFor="filter">Filter (leave empty to show all entries):</label>
      <input
        type="text"
        id="filter"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      {!error ? null : <div className="error">{String(error)}</div>}
      {isLoading
        ? null
        : data?.map((webhook) => (
            <>
              <hr />
              <p>Date: {webhook.date.toISOString()}</p>
              <pre>{JSON.stringify(webhook.data, null, 2)}</pre>
            </>
          ))}
    </>
  );
}
