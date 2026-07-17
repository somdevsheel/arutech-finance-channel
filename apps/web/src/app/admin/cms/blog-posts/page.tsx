import type { Metadata } from "next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { getBlogPosts } from "@/lib/admin/session";
import { createBlogPostAction } from "@/lib/admin/actions";
import { AdminCreateForm } from "@/components/admin/admin-create-form";
import { BlogPostActions } from "@/components/admin/blog-post-actions";

export const metadata: Metadata = {
  title: "CMS — Blog Posts",
  robots: { index: false, follow: false },
};

export default async function AdminBlogPostsPage() {
  const posts = await getBlogPosts();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">CMS — Blog Posts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Only published posts appear on the public site at /blog.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Post</CardTitle>
        </CardHeader>
        <CardContent>
          <AdminCreateForm action={createBlogPostAction} className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="slug">Slug</Label>
              <Input id="slug" name="slug" required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="title">Title</Label>
              <Input id="title" name="title" required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="author">Author</Label>
              <Input id="author" name="author" defaultValue="Arutech Editorial Team" required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="reading_minutes">Reading Minutes</Label>
              <Input id="reading_minutes" name="reading_minutes" defaultValue="5" inputMode="numeric" />
            </div>
            <div className="sm:col-span-2 space-y-1.5">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input id="tags" name="tags" placeholder="Credit Score, Personal Finance" />
            </div>
            <div className="sm:col-span-2 space-y-1.5">
              <Label htmlFor="excerpt">Excerpt</Label>
              <Textarea id="excerpt" name="excerpt" rows={2} required />
            </div>
            <div className="sm:col-span-2 space-y-1.5">
              <Label htmlFor="body">Body</Label>
              <Textarea id="body" name="body" rows={5} required />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit">Create Draft</Button>
            </div>
          </AdminCreateForm>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Posts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Published</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {posts.map((post) => (
                  <TableRow key={post.id}>
                    <TableCell className="font-medium">{post.title}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {post.published_at ? formatDate(post.published_at) : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={post.is_published ? "secondary" : "outline"}>
                        {post.is_published ? "Published" : "Draft"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <BlogPostActions postId={post.id} isPublished={post.is_published} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
