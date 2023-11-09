import IframeResizer from 'iframe-resizer-react'
import { useStore } from "./StoreProvider";

const style = {
    wrapper: {
        "text-align": "center",
        "margin": "10px",
        "height": "100vh"
    },
    portal: {
        "min-width": "85%",
        "width": "1px",
        "border": "0px",
        "height": "100%",
        "padding": "5px"
    }
}


export default function GradioPortal({ src }: {src: string}) {
    const { theme } = useStore();

    return (
        <div style={style.wrapper}>
            <IframeResizer src={src + "/?__theme=" + theme} style={style.portal} />
        </div>
    )

}
