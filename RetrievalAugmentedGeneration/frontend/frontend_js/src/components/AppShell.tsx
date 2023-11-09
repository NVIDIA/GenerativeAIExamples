import { useStore } from "./StoreProvider";
import { css, theme } from "@kui-shared/styles";
import { ThemeProvider } from "@kui-react/theme";
import { PropsWithChildren } from "react";

export const NAVBAR_HEIGHT = 3;

/**
 * Root Container
 */
const RootStyles = css({
  display: "grid",
  flexGrow: 1,
  gridTemplateAreas:
    "'navbar navbar'" + "'sidebar content'" + "'sidebar footer'",
  gridTemplateRows: "3rem auto 1fr auto",
  "@lg": {
    gridTemplateAreas:
      "'navbar navbar'" +
      "'sidebar content'" +
      "'sidebar footer'",
    gridTemplateColumns: "15rem 1fr",
    gridTemplateRows: "3rem auto 1fr auto",
  },
  variants: {
    isCollapsed: {
      true: {
        gridTemplateColumns: `0px 1fr auto`,
      },
      false: {
        gridTemplateColumns: `0px 1fr auto`,
        // gridTemplateColumns: "15rem 1fr auto",
      },
    },
  },
});

export const Root = ({ children }: PropsWithChildren) => {
  const { collapsed, theme } = useStore();

  return (
    <ThemeProvider theme={theme} withCanvas withReset>
      <div className={RootStyles({ isCollapsed: collapsed })}>{children}</div>
    </ThemeProvider>
  );
};

/**
 * Navbar Container
 */
const NavbarStyles = css({
  gridArea: "navbar",
  height: `${NAVBAR_HEIGHT}rem`,
  // color
  backgroundColor: theme.colors.displayBgLow,
  borderBottom: `1px solid ${theme.colors.displayBorderStatic}`,
  // position
  position: "sticky",
  top: 0,
  zIndex: 10,
});

export const NavbarContainer = ({ children }: PropsWithChildren) => {
  return <div className={NavbarStyles()}>{children}</div>;
};

/**
 * Content Container
 */
const ContentStyles = css({
  gridArea: "content",
});

export const ContentContainer = ({ children }: PropsWithChildren) => {
  return <div className={ContentStyles()}>{children}</div>;
};
