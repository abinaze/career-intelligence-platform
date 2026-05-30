"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

/**
 * TanStack Query provider with production-safe defaults.
 *
 * Configured with:
 * - 1 minute stale time to reduce unnecessary refetches
 * - No retry on 4xx client errors
 * - Devtools only in development
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            gcTime: 5 * 60 * 1000,
            retry: (failureCount, error) => {
              if (
                error instanceof Error &&
                "status" in error &&
                typeof (error as { status: number }).status === "number" &&
                (error as { status: number }).status >= 400 &&
                (error as { status: number }).status < 500
              ) {
                return false;
              }
              return failureCount < 2;
            },
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
