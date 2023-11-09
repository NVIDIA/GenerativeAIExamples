import { Inline } from "@kui-react/inline";
import { Logo } from "@kui-react/logo";

import { AppBar } from "@kui-react/app-bar";
import NavbarLink from "./NavbarLink";
import { Button } from "@kui-react/button";
import { MiscMoon, ImageSunHigh } from "@nv-brand-assets/react-icons-inline";
import { useStore } from "./StoreProvider";

export const Navbar = () => {
  const { theme, setTheme } = useStore();

  const toggleThemeName = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const logoName = () => {
    if (theme == "light") {
      return ("all_black_text_horizontal")
    } else {
      return ("all_white_text_horizontal")
    }
  }


  return (
    <AppBar
      slotLogo={<Logo name={logoName()} />}
      slotLeft="LLM Playground"
      slotRight={
        <Inline gap="none" css={{ height: "100%" , padding: "0 25px 0 0"}}>
          <NavbarLink label="converse" to="/converse" />
          <NavbarLink label="knowledge base" to="/kb" />

          <Button tone="tertiary" onClick={toggleThemeName}>
            {theme === "dark" ? (
              <MiscMoon variant="line" />
            ) : (
              <ImageSunHigh variant="line" />
            )}
          </Button>

        </Inline>
      }
    />
    );
  };
