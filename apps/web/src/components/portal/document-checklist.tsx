"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
import { submitDocumentAction } from "@/lib/loans/actions";
import type { LoanDocument, LoanDocumentStatus } from "@/types/loans";

const STATUS_META: Record<
  LoanDocumentStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { label: "Not submitted", variant: "secondary" },
  submitted: { label: "Submitted", variant: "outline" },
  verified: { label: "Verified", variant: "default" },
  rejected: { label: "Rejected", variant: "destructive" },
};

function DocumentRow({
  applicationId,
  document,
}: {
  applicationId: string;
  document: LoanDocument;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const meta = STATUS_META[document.status];

  function handleSubmit() {
    startTransition(async () => {
      const result = await submitDocumentAction(applicationId, document.id);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      router.refresh();
    });
  }

  return (
    <TableRow>
      <TableCell>{document.document_type}</TableCell>
      <TableCell>
        <Badge variant={meta.variant}>{meta.label}</Badge>
      </TableCell>
      <TableCell className="text-right">
        {document.status === "pending" && (
          <Button type="button" size="sm" variant="outline" disabled={isPending} onClick={handleSubmit}>
            {isPending ? "Marking..." : "Mark as submitted"}
          </Button>
        )}
      </TableCell>
    </TableRow>
  );
}

export function DocumentChecklist({
  applicationId,
  documents,
}: {
  applicationId: string;
  documents: LoanDocument[];
}) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableBody>
          {documents.map((document) => (
            <DocumentRow key={document.id} applicationId={applicationId} document={document} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
