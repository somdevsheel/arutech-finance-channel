import type { Metadata } from "next";
import { Briefcase, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SectionHeading } from "@/components/marketing/section-heading";
import { jobOpenings } from "@/content/job-openings";

export const metadata: Metadata = {
  title: "Careers",
  description:
    "Open roles at Arutech Finance Platform, across engineering, credit and risk, partnerships, and operations.",
};

export default function CareersPage() {
  return (
    <>
      <section className="border-b bg-muted/30">
        <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            Help us fix how India borrows
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            We&apos;re a small team working on a genuinely hard problem:
            matching borrowers to the right lender, quickly and honestly.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8">
        <SectionHeading title="Open Positions" align="left" className="mx-0" />
        <div className="mt-10 space-y-4">
          {jobOpenings.map((job) => (
            <Card key={job.slug}>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-lg">{job.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {job.description}
                    </CardDescription>
                  </div>
                  <Badge variant="secondary">{job.type}</Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Briefcase className="size-4" /> {job.department}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <MapPin className="size-4" /> {job.location}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 sm:grid-cols-2">
                  <div>
                    <h3 className="text-sm font-semibold">Responsibilities</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-muted-foreground">
                      {job.responsibilities.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">Requirements</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-muted-foreground">
                      {job.requirements.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <Button
                  className="mt-6"
                  render={
                    <a
                      href={`mailto:careers@arutech.com?subject=Application: ${job.title}`}
                    />
                  }
                >
                  Apply for this role
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-muted-foreground">
          Don&apos;t see a role that fits? Write to us at{" "}
          <a href="mailto:careers@arutech.com" className="underline underline-offset-2">
            careers@arutech.com
          </a>{" "}
          with what you&apos;re looking for.
        </p>
      </section>
    </>
  );
}
