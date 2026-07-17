"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { deleteBlogPostAction, setBlogPostPublishedAction } from "@/lib/admin/actions";

export function BlogPostActions({
  postId,
  isPublished,
}: {
  postId: string;
  isPublished: boolean;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function togglePublish() {
    startTransition(async () => {
      const result = await setBlogPostPublishedAction(postId, !isPublished);
      if (!result.ok) toast.error(result.error);
      else router.refresh();
    });
  }

  function handleDelete() {
    if (!confirm("Delete this post? This cannot be undone.")) return;
    startTransition(async () => {
      const result = await deleteBlogPostAction(postId);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      router.refresh();
    });
  }

  return (
    <div className="flex justify-end gap-2">
      <Button type="button" size="sm" variant="outline" disabled={isPending} onClick={togglePublish}>
        {isPublished ? "Unpublish" : "Publish"}
      </Button>
      <Button type="button" size="sm" variant="ghost" disabled={isPending} onClick={handleDelete}>
        Delete
      </Button>
    </div>
  );
}
