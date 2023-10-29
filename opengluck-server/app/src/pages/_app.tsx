import "@/styles/globals.css";
import type { AppProps } from "next/app";
import EnsureLoggedIn from "@/components/EnsureLoggedIn";
import { QueryClient, QueryClientProvider } from "react-query";
const queryClient = new QueryClient();

export default function App({
  Component,
  pageProps: { session, ...pageProps },
}: AppProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <EnsureLoggedIn>
        <Component {...pageProps} />
      </EnsureLoggedIn>
    </QueryClientProvider>
  );
}
