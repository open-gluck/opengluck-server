import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        <Main />
        <NextScript />
        <footer>
          This is{" "}
          <a href="https://opengluck.com" target="_blank">
            OpenGlück Server
          </a>{" "}
          - v1.0 -{" "}
          <a
            href="http://github.com/open-gluck/opengluck-server/wiki"
            target="_blank"
          >
            Help
          </a>{" "}
          -{" "}
          <a href="http://github.com/open-gluck/" target="_blank">
            GitHub
          </a>
        </footer>
      </body>
    </Html>
  );
}
