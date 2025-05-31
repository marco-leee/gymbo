import { useMantineColorScheme } from "@mantine/core";
import { createContext, useContext } from "react";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export type Config = {
	theme: "light" | "dark" | "system";
};

interface ConfigState extends Config {
	setTheme: (theme: "light" | "dark" | "system") => void;
}

export default function useConfig() {
	const colourScheme = useMantineColorScheme();

	return create<ConfigState>()(
		persist(
			(set, get) => ({
				...(get() as Config),
				setTheme: (theme) => {
					set({ ...get(), theme });
					colourScheme.setColorScheme(theme === "system" ? "auto" : theme);
				},
			}),
			{ name: "config", storage: createJSONStorage(() => localStorage) }
		)
	);
}

const ConfigContext = createContext<ConfigState | undefined>(undefined);

export const ConfigProvider = ({ children }: { children: React.ReactNode }) => {
	const configStore = useConfig();
	const config = configStore();
	return <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>;
};

export const useConfigContext = () => {
	const config = useContext(ConfigContext);

	if (!config) {
		throw new Error("useConfigContext must be used within a ConfigProvider");
	}

	return config;
};
