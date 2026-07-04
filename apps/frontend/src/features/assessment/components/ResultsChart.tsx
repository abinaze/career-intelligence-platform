"use client";

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { DimensionScore } from "../types";

interface ResultsChartProps {
  scores: DimensionScore[];
}

// Shorten long dimension names so they fit on the radar axes
function shortenLabel(name: string): string {
  const map: Record<string, string> = {
    Openness: "Open.",
    Conscientiousness: "Consc.",
    Extraversion: "Extra.",
    Agreeableness: "Agree.",
    Neuroticism: "Neuro.",
    Realistic: "Real.",
    Investigative: "Invest.",
    Artistic: "Artist.",
    Social: "Social",
    Enterprising: "Enterp.",
    Conventional: "Conv.",
  };
  return map[name] ?? name.slice(0, 6) + ".";
}

export function ResultsChart({ scores }: ResultsChartProps) {
  const data = scores.map((s) => ({
    dimension: shortenLabel(s.display_name),
    fullName: s.display_name,
    score: Math.round(s.score),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{
              fill: "hsl(var(--muted-foreground))",
              fontSize: 11,
              fontWeight: 500,
            }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.25}
            strokeWidth={2}
          />
          <Tooltip
            formatter={(value) => [
              `${Math.round(Number(value))}/100`,
              "",
            ]}
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.5rem",
              fontSize: "12px",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
