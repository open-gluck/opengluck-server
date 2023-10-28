import Head from "next/head";
import styles from "@/styles/Home.module.css";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <Head>
        <title>OpenGlück</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className={styles.main}>
        <h1>OpenGlück</h1>
        <h2>Data</h2>
        <h3>
          <Link href="/current">Current Data</Link>
        </h3>
        View current data.
        <h3>
          <Link href="/last">Last Data</Link>
        </h3>
        View past data.
        <h3>
          <Link href="/export">Export Data</Link>
        </h3>
        Export past data.
        <h2>Glucose Records</h2>
        <h3>
          <Link href="/glucose-record">Glucose Records</Link>
        </h3>
        View past glucose records.
        <h2>Instant Glucose Records</h2>
        <h3>
          <Link href="/instant-glucose-record">Instant Glucose Records</Link>
        </h3>
        View past instant glucose records.
        <h2>Episodes</h2>
        <h3>
          <Link href="/episode">Episodes</Link>
        </h3>
        View past episodes.
        <h2>Revision</h2>
        <h3>
          <Link href="/revision">View current revision</Link>
        </h3>
        View the current revision info.
        <h2>Configuration</h2>
        <h3>
          <Link href="/webhooks">Webhooks</Link>
        </h3>
        Configure the webhooks. This is where you can connect other tools (
        <a href="https://zapier.com/">Zapier</a>,{" "}
        <a href="https://ifttt.com/">IFTTT</a>, etc) to OpenGlück. .
        <h2>Admin</h2>
        <h3>
          <Link href="/users">Users Administration</Link>
        </h3>
        Add or remove users.
        <h2>Developer Tools</h2>
        <h3>
          <Link href="/last-requests">
            View Last HTTP Requests To OpenGlück
          </Link>
        </h3>
        This page shows the last 500 HTTP requests sent to OpenGlück. Useful for
        debugging, or when you are building something new.
        <h3>
          <Link href="/userdata">View UserData</Link>
        </h3>
        This page shows the active UserData.
        <h3>
          <Link href="/api-explorer">API Explorer</Link>
        </h3>
        This page allows you to send network request and see their response.
        <h2>Logout</h2>
        <h3>
          <Link href="/logout">Logout</Link>
        </h3>
      </main>
    </>
  );
}
