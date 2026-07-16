"use client";

import { motion } from "motion/react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  usePlatformLiveness,
  usePlatformReadiness,
} from "@/hooks/use-platform-health";

function StatusBadge({ status }: { status: string | undefined }) {
  if (!status) {
    return <Skeleton className="h-5 w-16" />;
  }

  const isOk = status === "ok";
  return (
    <Badge variant={isOk ? "default" : "destructive"}>
      {isOk ? "Operational" : "Degraded"}
    </Badge>
  );
}

export function SystemStatusCard() {
  const liveness = usePlatformLiveness();
  const readiness = usePlatformReadiness();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Card className="w-full max-w-xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Platform Status</CardTitle>
            <StatusBadge status={liveness.data?.status} />
          </div>
          <CardDescription>
            Live signal from the API foundation service.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">API service</span>
            <span className="font-mono">
              {liveness.data?.service ?? "arutech-api"}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">API version</span>
            <span className="font-mono">{liveness.data?.version ?? "—"}</span>
          </div>
          <div className="border-t pt-3">
            <p className="mb-2 text-sm text-muted-foreground">
              Dependency checks
            </p>
            {readiness.isLoading && (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            )}
            {readiness.data && (
              <ul className="space-y-1.5">
                {Object.entries(readiness.data.checks).map(
                  ([name, status]) => (
                    <li
                      key={name}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="capitalize">{name}</span>
                      <StatusBadge status={status} />
                    </li>
                  ),
                )}
              </ul>
            )}
            {readiness.isError && (
              <p className="text-sm text-destructive">
                Unable to reach the readiness endpoint.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
