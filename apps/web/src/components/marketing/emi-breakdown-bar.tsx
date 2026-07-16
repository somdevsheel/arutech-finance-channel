import { formatInr } from "@/lib/format";

/**
 * A single part-to-whole bar (principal vs. interest). Segments are
 * distinguished by lightness alone (no hue), so it reads correctly
 * regardless of color vision — and every segment carries an explicit
 * label + value rather than relying on the color swatch alone.
 */
export function EmiBreakdownBar({
  principal,
  totalInterest,
}: {
  principal: number;
  totalInterest: number;
}) {
  const total = principal + totalInterest;
  const principalPercent = total > 0 ? (principal / total) * 100 : 0;
  const interestPercent = 100 - principalPercent;

  return (
    <div>
      <div className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${principalPercent}%` }}
        />
        <div
          className="h-full rounded-full bg-primary/30"
          style={{ width: `${interestPercent}%` }}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1.5 text-sm">
        <div className="flex items-center gap-2">
          <span className="size-2.5 rounded-full bg-primary" />
          <span className="text-muted-foreground">Principal</span>
          <span className="font-medium">{formatInr(principal)}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="size-2.5 rounded-full bg-primary/30" />
          <span className="text-muted-foreground">Total Interest</span>
          <span className="font-medium">{formatInr(totalInterest)}</span>
        </div>
      </div>
    </div>
  );
}
