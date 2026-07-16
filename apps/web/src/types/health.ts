export interface LivenessResponse {
  status: "ok";
  service: string;
  version: string;
}

export type DependencyStatus = "ok" | "error";

export interface ReadinessResponse {
  status: DependencyStatus;
  checks: Record<string, DependencyStatus>;
}
