export default function ChartImage({ b64, alt }: { b64: string; alt: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-semibold text-gray-500 mb-2">{alt}</p>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`data:image/png;base64,${b64}`} alt={alt} className="w-full rounded" />
    </div>
  );
}
