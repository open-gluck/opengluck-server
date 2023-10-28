import { webhookTypes } from "@/features/webhooks";
import Link from "next/link";

export default function Webhooks() {
  return (
    <>
      <h2>Webhooks</h2>
      {webhookTypes.map((webhookType) => (
        <>
          <h3>
            <Link href="/webhooks/[id]" as={`/webhooks/${webhookType.id}`}>
              {webhookType.name}
            </Link>
          </h3>
          <div>{webhookType.description}</div>
        </>
      ))}
    </>
  );
}
