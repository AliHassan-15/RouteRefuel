import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { suggestPlaces, type PlaceSuggestion } from "../api/client";

interface PlaceAutocompleteProps {
  id: string;
  name: string;
  label: string;
  value: string;
  disabled?: boolean;
  placeholder?: string;
  error?: string;
  hintId?: string;
  onChange: (value: string) => void;
}

export function PlaceAutocomplete({
  id,
  name,
  label,
  value,
  disabled = false,
  placeholder,
  error,
  hintId,
  onChange,
}: PlaceAutocompleteProps) {
  const listboxId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const requestIdRef = useRef(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<PlaceSuggestion[]>([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [focused, setFocused] = useState(false);
  const [fetchedFor, setFetchedFor] = useState("");
  const skipFetchRef = useRef(false);

  useEffect(() => {
    function onDocMouseDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, []);

  useEffect(() => {
    if (skipFetchRef.current) {
      skipFetchRef.current = false;
      return;
    }

    const q = value.trim();
    // Drop previous suggestions immediately so stale cities never linger.
    setItems([]);
    setActiveIndex(-1);
    setFetchedFor("");

    if (disabled || q.length < 1) {
      setOpen(false);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setOpen(focused);

    const timer = window.setTimeout(async () => {
      try {
        const suggestions = await suggestPlaces(q, controller.signal);
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }
        setItems(suggestions);
        setFetchedFor(q);
        setOpen(focused);
        setActiveIndex(suggestions.length > 0 ? 0 : -1);
      } catch {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }
        setItems([]);
        setFetchedFor(q);
        setOpen(focused);
        setActiveIndex(-1);
      } finally {
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setLoading(false);
        }
      }
    }, 120);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [value, disabled, focused]);

  const pick = useCallback(
    (item: PlaceSuggestion) => {
      skipFetchRef.current = true;
      onChange(item.label);
      setItems([]);
      setFetchedFor(item.label);
      setOpen(false);
      setActiveIndex(-1);
      setLoading(false);
    },
    [onChange]
  );

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!open || items.length === 0) {
      if (event.key === "Escape") setOpen(false);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (i + 1) % items.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (i <= 0 ? items.length - 1 : i - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      pick(items[activeIndex]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      setActiveIndex(-1);
    }
  }

  const errorId = error ? `${id}-error` : undefined;
  const q = value.trim();
  const resultsAreFresh = fetchedFor === q;
  const showMenu = open && focused && q.length > 0 && (loading || resultsAreFresh);
  const showEmpty =
    showMenu && !loading && resultsAreFresh && items.length === 0;

  return (
    <div ref={rootRef} className="relative">
      <label
        htmlFor={id}
        className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-mist uppercase"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          name={name}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
          role="combobox"
          aria-expanded={showMenu && items.length > 0}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={
            activeIndex >= 0 ? `${listboxId}-opt-${activeIndex}` : undefined
          }
          aria-invalid={Boolean(error)}
          aria-describedby={errorId ?? hintId}
          className="field-input pr-9 text-base sm:text-sm"
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => {
            setFocused(true);
            if (resultsAreFresh && (items.length > 0 || q.length > 0)) {
              setOpen(true);
            }
          }}
          onBlur={() => {
            window.setTimeout(() => setFocused(false), 150);
          }}
          onKeyDown={onKeyDown}
        />
        <span
          className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-[10px] text-mist"
          aria-hidden="true"
        >
          {loading ? "…" : "▾"}
        </span>
      </div>

      {showMenu && items.length > 0 ? (
        <ul
          id={listboxId}
          role="listbox"
          className="suggest-menu absolute inset-x-0 top-[calc(100%+4px)] z-50 max-h-72 overflow-y-auto py-1"
        >
          {items.map((item, index) => {
            const active = index === activeIndex;
            return (
              <li
                key={`${item.label}-${item.latitude}-${item.longitude}`}
                id={`${listboxId}-opt-${index}`}
                role="option"
                aria-selected={active}
                className={`suggest-option cursor-pointer px-3 py-2 text-sm ${
                  active ? "suggest-option-active" : ""
                }`}
                onMouseEnter={() => setActiveIndex(index)}
                onMouseDown={(e) => {
                  e.preventDefault();
                  pick(item);
                }}
              >
                <span className="font-medium text-paper">{item.city}</span>
                <span className="text-mist">, {item.state}</span>
              </li>
            );
          })}
        </ul>
      ) : null}

      {showEmpty ? (
        <div className="suggest-menu absolute inset-x-0 top-[calc(100%+4px)] z-50 px-3 py-2.5 text-xs text-mist">
          No matching USA cities
        </div>
      ) : null}

      {error ? (
        <p id={errorId} className="mt-1.5 text-xs text-danger-soft" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
