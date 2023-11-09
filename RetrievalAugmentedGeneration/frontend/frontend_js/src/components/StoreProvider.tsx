import { ThemeProps } from "@kui-react/theme";
import { useMediaQuery } from "@kui-react/utils";
import React, {
  createContext,
  Dispatch,
  PropsWithChildren,
  SetStateAction,
  useContext,
  useEffect,
  useState,
} from "react";

export type StoreContextProps = {
  // collapsed
  collapsed: boolean;
  setCollapsed: Dispatch<SetStateAction<boolean>>;
  // themes
  theme: ThemeProps["theme"];
  setTheme: Dispatch<SetStateAction<ThemeProps["theme"]>>;
};

export const StoreContext = createContext<StoreContextProps>({
  // collapsed
  collapsed: false,
  setCollapsed: () => null,
  // themes
  theme: "light",
  setTheme: () => null,
});

const COLLAPSED_KEY = "is-kui-collapsed";
const THEME_KEY = "is-kui-theme-dark-mode-enabled";

export const useStore = () => useContext(StoreContext);

export const StoreProvider = ({ children }: PropsWithChildren) => {
  const [_mounted, _setMounted] = useState(false);

  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [theme, setTheme] = useState<ThemeProps["theme"]>("light");

  const isMdBreakpoint = useMediaQuery("md");

  useEffect(() => {
    _setMounted(true);

    const _collapsed = window.localStorage.getItem(COLLAPSED_KEY);
    const _theme = window.localStorage.getItem(THEME_KEY);

    if (_collapsed !== null) setCollapsed(JSON.parse(_collapsed));
    if (_theme !== null) setTheme(JSON.parse(_theme));
  }, []);

  useEffect(() => {
    if (isMdBreakpoint) {
      setCollapsed(true);
    } else {
      setCollapsed(false);
    }
  }, [isMdBreakpoint]);

  useEffect(() => {
    window.localStorage.setItem(COLLAPSED_KEY, JSON.stringify(collapsed));
  }, [collapsed]);

  useEffect(() => {
    window.localStorage.setItem(THEME_KEY, JSON.stringify(theme));
  }, [theme]);

  return (
    <StoreContext.Provider
      value={{
        collapsed,
        setCollapsed,
        theme,
        setTheme,
      }}
    >
      {_mounted && children}
    </StoreContext.Provider>
  );
};
