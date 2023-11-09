import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { StoreProvider } from "../components/StoreProvider";
import {
  ContentContainer,
  NavbarContainer,
  Root,
} from "../components/AppShell";
import { Navbar } from "../components/Navbar";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <StoreProvider>
      <Root>
        <NavbarContainer>
          <Navbar />
        </NavbarContainer>
        <ContentContainer>
          <Component {...pageProps} />
        </ContentContainer>
      </Root>
    </StoreProvider>
  );
}
