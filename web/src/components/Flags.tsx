import { directionText, rmseText } from "../format";

/** The two stored baseline flags, in plain words. Amber = does not beat, green = beats. */
export default function Flags({ rmse, direction }: { rmse: boolean; direction: boolean }) {
  const item = (beats: boolean, text: string) => (
    <li
      className={`flex items-start gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium ${
        beats ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"
      }`}
    >
      <span aria-hidden className="font-bold">{beats ? "✓" : "!"}</span>
      <span>{text}</span>
    </li>
  );
  return (
    <ul className="space-y-1.5">
      {item(rmse, rmseText(rmse))}
      {item(direction, directionText(direction))}
    </ul>
  );
}
