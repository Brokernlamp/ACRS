"use client";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function PlotlyChart({ data, title }: { data: object; title?: string }) {
  const fig = data as { data: Plotly.Data[]; layout: Partial<Plotly.Layout> };
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      {title && <p className="text-xs font-semibold text-gray-500 mb-2">{title}</p>}
      <Plot
        data={fig.data}
        layout={{
          ...fig.layout,
          autosize: true,
          margin: { l: 50, r: 20, t: 40, b: 50 },
          font: { family: "Inter, sans-serif", size: 12 },
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", minHeight: 320 }}
        useResizeHandler
      />
    </div>
  );
}
