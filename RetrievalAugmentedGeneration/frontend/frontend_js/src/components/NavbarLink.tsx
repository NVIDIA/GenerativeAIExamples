import Link from "next/link";

import { HorizontalNavItem } from "@kui-react/horizontal-nav";


export default function NavbarLink({label, to }: {label: string, to: string}) {

  return (
    <Link href={to} passHref legacyBehavior>
      <HorizontalNavItem
        selected={window.location.pathname == to}
        css={{ height: "100%" , width: "unset"}}
        >

        <span style={{ textTransform: "capitalize" }}>{label}</span>
      </HorizontalNavItem>
    </Link>
    )
  };
