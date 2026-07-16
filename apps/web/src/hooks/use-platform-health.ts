"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import type { LivenessResponse, ReadinessResponse } from "@/types/health";

export function usePlatformLiveness() {
  return useQuery({
    queryKey: ["health", "live"],
    queryFn: () => apiFetch<LivenessResponse>("/api/v1/health"),
    refetchInterval: 30_000,
  });
}

export function usePlatformReadiness() {
  return useQuery({
    queryKey: ["health", "ready"],
    queryFn: () => apiFetch<ReadinessResponse>("/api/v1/health/ready"),
    refetchInterval: 30_000,
  });
}
