import Head from "next/head";
import "../styles/globals.css";

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>Rox Zone</title>
        <meta
          name="description"
          content="Rox Zone is a HYROX, Cardio Lab, diet, and AI coaching performance planner."
        />
      </Head>
      <Component {...pageProps} />
    </>
  );
}
