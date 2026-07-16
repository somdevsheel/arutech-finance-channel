import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SystemStatusCard } from "@/components/system-status-card";

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("SystemStatusCard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders operational status once liveness and readiness resolve", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/health/ready")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              status: "ok",
              checks: { database: "ok", redis: "ok" },
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({ status: "ok", service: "arutech-api", version: "0.1.0" }),
          { status: 200 },
        ),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithClient(<SystemStatusCard />);

    // One top-level badge plus one per dependency check (database, redis).
    expect(await screen.findAllByText("Operational")).toHaveLength(3);

    await waitFor(() => {
      expect(screen.getByText("arutech-api")).toBeInTheDocument();
    });

    expect(screen.getByText("database")).toBeInTheDocument();
    expect(screen.getByText("redis")).toBeInTheDocument();
  });

  it("shows a degraded badge when the API reports an error status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ status: "error", service: "arutech-api", version: "0.1.0" }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    renderWithClient(<SystemStatusCard />);

    expect(await screen.findByText("Degraded")).toBeInTheDocument();
  });
});
