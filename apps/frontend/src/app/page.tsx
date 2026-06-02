import Link from "next/link";

/**
 * Home / landing page.
 * Route: /
 *
 * Minimal landing page that routes visitors to login or register.
 * Will be expanded into a full marketing page in a later commit.
 */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      {/* Background */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-background" />
        <div className="absolute left-1/2 top-1/4 h-[800px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/5 blur-3xl" />
      </div>

      <div className="mx-auto max-w-3xl text-center">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg">
            <span className="text-2xl font-bold text-primary-foreground">C</span>
          </div>
        </div>

        {/* Headline */}
        <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
          Your AI-Powered{" "}
          <span className="text-primary">Career Intelligence</span>{" "}
          Platform
        </h1>

        <p className="mt-6 text-lg leading-8 text-muted-foreground">
          Discover careers that match your personality, cognition, and ambitions
          through deep behavioral analysis and AI-driven recommendations.
        </p>

        {/* CTA buttons */}
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/register"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-8 py-3 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            Get started free
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-lg border border-border px-8 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
          >
            Sign in
          </Link>
        </div>

        {/* Feature highlights */}
        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {[
            {
              title: "Psychometric Analysis",
              description:
                "17-dimension personality and cognitive scoring based on validated assessment models.",
            },
            {
              title: "AI Recommendations",
              description:
                "Career paths ranked by compatibility with explainable confidence scores.",
            },
            {
              title: "100% Free",
              description:
                "Built entirely on open-source technology. No subscriptions, no credit card.",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-border/50 bg-card p-6 text-left"
            >
              <h3 className="font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
