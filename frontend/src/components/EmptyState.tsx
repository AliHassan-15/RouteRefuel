const FEATURES = [
  {
    title: "Real driving path",
    body: "OSM/OSRM geometry — not a straight line between cities.",
  },
  {
    title: "Cost-first stops",
    body: "Cheapest reachable stations within a 500-mile tank, not the nearest pump.",
  },
  {
    title: "Auditable math",
    body: "Per-stop gallons × price roll up to the trip total you can verify.",
  },
] as const;

export function EmptyState() {
  return (
    <div
      className="animate-fade-up flex h-full min-h-[300px] flex-col gap-4"
      aria-labelledby="empty-heading"
    >
      <div>
        <p className="mb-1.5 text-[11px] font-semibold tracking-[0.14em] text-fuel uppercase">
          Ready when you are
        </p>
        <h2
          id="empty-heading"
          className="font-display text-[1.35rem] leading-snug font-semibold text-paper sm:text-2xl"
        >
          Plan the route.
          <span className="block text-mist-bright/90">Spend less on fuel.</span>
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-mist sm:text-[13px]">
          Enter a USA start and finish. RouteRefuel draws the drive, picks
          cost-optimal truck stops along the corridor, and shows every dollar
          before you leave the yard.
        </p>
      </div>

      <ul className="space-y-2" role="list">
        {FEATURES.map((feature, index) => (
          <li
            key={feature.title}
            className={`elevated-inset interactive-lift animate-fade-up flex gap-3 px-3 py-2.5 stagger-${index + 1}`}
          >
            <span
              className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-fuel/15 font-mono text-xs font-semibold text-fuel"
              aria-hidden="true"
            >
              {index + 1}
            </span>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-paper">{feature.title}</div>
              <div className="text-xs leading-relaxed text-mist">{feature.body}</div>
            </div>
          </li>
        ))}
      </ul>

      <div className="elevated-inset mt-auto grid grid-cols-3 gap-2 px-3 py-2.5">
        {[
          ["Range", "500 mi"],
          ["Economy", "10 MPG"],
          ["Tank", "50 gal"],
        ].map(([label, value]) => (
          <div key={label}>
            <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
              {label}
            </div>
            <div className="mt-0.5 font-mono text-sm font-semibold text-paper">
              {value}
            </div>
          </div>
        ))}
      </div>

      <p className="text-[11px] text-mist">
        Try{" "}
        <span className="font-medium text-mist-bright">
          Chicago, IL → Dallas, TX
        </span>{" "}
        for a multi-stop plan in a few seconds.
      </p>
    </div>
  );
}
