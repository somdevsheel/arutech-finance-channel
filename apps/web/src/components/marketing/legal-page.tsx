export interface LegalSection {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
}

export function LegalPage({
  title,
  effectiveDate,
  intro,
  sections,
}: {
  title: string;
  effectiveDate: string;
  intro: string;
  sections: LegalSection[];
}) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-20 sm:px-6 lg:px-8">
      <h1 className="text-4xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Effective date: {effectiveDate}
      </p>
      <p className="mt-6 text-muted-foreground">{intro}</p>

      <div className="mt-10 space-y-10">
        {sections.map((section) => (
          <div key={section.heading}>
            <h2 className="text-xl font-semibold">{section.heading}</h2>
            <div className="mt-3 space-y-3 text-sm text-muted-foreground">
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
              {section.bullets && (
                <ul className="list-disc space-y-1.5 pl-5">
                  {section.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
