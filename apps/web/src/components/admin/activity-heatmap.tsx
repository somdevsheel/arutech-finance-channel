import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ActivityHeatmap as ActivityHeatmapData } from "@/types/dashboard";

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function ActivityHeatmap({ heatmap }: { heatmap: ActivityHeatmapData }) {
  const totals = heatmap.cells.map((cell) => cell.lead_count + cell.application_count);
  const maxTotal = Math.max(1, ...totals);

  const grid: number[][] = Array.from({ length: 7 }, () => Array(24).fill(0));
  for (const cell of heatmap.cells) {
    grid[cell.day_of_week]![cell.hour] = cell.lead_count + cell.application_count;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Heatmap</CardTitle>
        <p className="text-xs text-muted-foreground">
          Leads and loan applications created, by day of week and hour.
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="inline-flex min-w-full flex-col gap-1">
            {grid.map((hours, dayIndex) => (
              <div key={dayIndex} className="flex items-center gap-1">
                <span className="w-8 shrink-0 text-xs text-muted-foreground">
                  {DAY_LABELS[dayIndex]}
                </span>
                <div className="flex gap-0.5">
                  {hours.map((count, hour) => (
                    <div
                      key={hour}
                      title={`${DAY_LABELS[dayIndex]} ${hour}:00 — ${count} event${count === 1 ? "" : "s"}`}
                      className="size-3 shrink-0 rounded-sm bg-primary"
                      style={{ opacity: count === 0 ? 0.06 : 0.25 + 0.75 * (count / maxTotal) }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
