import type { AppProps } from "next/app";
import "../semantic/dist/semantic.css";

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
export default MyApp;
