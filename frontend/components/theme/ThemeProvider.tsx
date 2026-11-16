"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useSyncExternalStore,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const STORAGE_KEY = "traceledger-theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getTheme(): Theme {
  return window.localStorage.getItem(STORAGE_KEY) === "dark"
    ? "dark"
    : "light";
}

function getServerTheme(): Theme {
  return "light";
}

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);

  return () => window.removeEventListener("storage", callback);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useSyncExternalStore(
    subscribe,
    getTheme,
    getServerTheme
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const toggleTheme = useCallback(() => {
    const nextTheme = theme === "light" ? "dark" : "light";

    window.localStorage.setItem(STORAGE_KEY, nextTheme);

    window.dispatchEvent(
      new StorageEvent("storage", {
        key: STORAGE_KEY,
        newValue: nextTheme,
      })
    );
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider.");
  }

  return context;
}
