import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export interface Config {
	theme: "light" | "dark" | "system";
}

interface ConfigState extends Config {
	setTheme: (theme: "light" | "dark" | "system") => void;
}

export default function useConfig() {
	return create<ConfigState>()(
		persist(
			(set, get) => ({
				...(get() as Config),
				setTheme: (theme) => set({ ...get(), theme }),
			}),
			{ name: "config", storage: createJSONStorage(() => localStorage) }
		)
	);
}
