interface ErrorStateProps {
  message: string;
  code?: string;
}

export function ErrorState({ message, code }: ErrorStateProps) {
  return (
    <div
      className="animate-fade-up flex min-h-[280px] flex-col gap-4 lg:min-h-[340px]"
      role="alert"
    >
      <div className="elevated-inset border border-danger/40 bg-danger/10 px-3.5 py-3.5 ring-1 ring-danger/25">
        <p className="text-[11px] font-semibold tracking-[0.14em] text-danger-soft uppercase">
          {code ?? "REQUEST_FAILED"}
        </p>
        <h2 className="font-display mt-1 text-xl font-semibold text-paper">
          Couldn’t plan this trip
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-mist sm:text-[13px]">
          {message}
        </p>
      </div>

      <div className="elevated-inset space-y-2 px-3 py-2.5 text-xs text-mist">
        <p className="font-semibold text-mist-bright">Try next</p>
        <ul className="list-disc space-y-1 pl-4">
          <li>Use a clear USA place like <span className="text-paper">City, ST</span></li>
          <li>Confirm both ends are inside the United States</li>
          <li>Retry in a moment if the routing service timed out</li>
        </ul>
      </div>

      <div className="elevated-inset mt-auto grid grid-cols-2 gap-2 px-3 py-2.5">
        <div>
          <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
            Coverage
          </div>
          <div className="mt-0.5 text-sm font-semibold text-paper">USA only</div>
        </div>
        <div>
          <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
            Format
          </div>
          <div className="mt-0.5 text-sm font-semibold text-paper">City, ST</div>
        </div>
      </div>
    </div>
  );
}
