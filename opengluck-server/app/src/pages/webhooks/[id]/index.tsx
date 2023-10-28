import { useRouter } from "next/router";
import { webhookTypes } from "@/features/webhooks";
import {
  useCreateWebhook,
  useDeleteWebhook,
  useGetWebhooks,
} from "@/features/api";
import { useCallback, useState } from "react";
import Link from "next/link";

export default function Webhook() {
  const router = useRouter();
  const webhookId = router.query.id as string;
  const webhookType = webhookTypes.find(
    (webhookType) => webhookType.id === webhookId
  );
  const { data, isLoading, error, refetch } = useGetWebhooks(webhookId);
  const [creating, setCreating] = useState(false);
  const createWebhook = useCreateWebhook();
  const deleteWebhook = useDeleteWebhook();

  const [url, setUrl] = useState("");
  const [filter, setFilter] = useState("");
  const [includeLast, setIncludeLast] = useState(false);
  const handleChangeUrl = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setUrl(e.target.value);
    },
    []
  );
  const handleChangeFilter = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFilter(e.target.value);
    },
    []
  );
  const handleChangeIncludeLast = useCallback(() => {
    setIncludeLast((val) => !val);
  }, []);
  const handleAdd = useCallback(async () => {
    console.log(" add");
    setCreating(true);
    if (!webhookType) {
      throw new Error("Cannot create webhook, unkonwn webhook");
    }
    await createWebhook({ webhook: webhookType.id, url, filter, includeLast });
    setCreating(false);
    refetch();
  }, [filter, includeLast, url, webhookType, createWebhook, refetch]);
  const handleDelete = useCallback(
    async (id: string) => {
      await deleteWebhook({ webhookId, id });
      refetch();
    },
    [deleteWebhook, webhookId, refetch]
  );

  if (!webhookType) {
    return <div>Webhook not found</div>;
  }
  if (isLoading || !data) {
    return null;
  }
  if (error) {
    console.log("got error", error);
    return <div>Error loading webhooks: {String(error)}</div>;
  }

  return (
    <>
      <h1>{webhookType.name} Webhook</h1>
      <p>{webhookType.description}</p>
      <Link href={`/webhooks/${webhookId}/view`}>View Last Payloads</Link>
      <table>
        <thead>
          <tr>
            <th>URL</th>
            <th>Filter</th>
            <th>Include Last?</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((webhook) => (
            <tr key={String(webhook.id)}>
              <td>{webhook.url}</td>
              <td>{webhook.filter}</td>
              <td>
                <input
                  type="checkbox"
                  disabled
                  checked={webhook.include_last}
                />
              </td>
              <td>
                <button onClick={() => handleDelete(webhook.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Add new webhook</h2>
      <form>
        <div>
          <label htmlFor="url">URL: </label>

          <input
            type="text"
            name="url"
            value={url}
            onChange={handleChangeUrl}
          />
        </div>
        <div>
          <label htmlFor="filter">
            Filter (in{" "}
            <a href="https://jmespath.org" target="_blank">
              JMESPath
            </a>
            ):{" "}
          </label>
          <input
            type="text"
            name="filter"
            value={filter}
            onChange={handleChangeFilter}
          />
        </div>
        <div>
          <input
            type="checkbox"
            name="include_last"
            checked={includeLast}
            onChange={handleChangeIncludeLast}
          />
          <label className="checkbox" htmlFor="include_last">
            Include Last Records
          </label>
        </div>
        <p>
          <button type="submit" onClick={handleAdd} disabled={creating}>
            Add
          </button>
        </p>
      </form>
    </>
  );
}
