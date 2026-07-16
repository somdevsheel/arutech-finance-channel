import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0a0a0a",
          color: "#fafafa",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 64, fontWeight: 600, display: "flex" }}>
          Arutech Finance
        </div>
        <div style={{ fontSize: 28, marginTop: 20, color: "#a1a1aa", display: "flex" }}>
          Compare & apply for loans from top banks and NBFCs
        </div>
      </div>
    ),
    { ...size },
  );
}
