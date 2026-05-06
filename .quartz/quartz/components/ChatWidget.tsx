import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { pathToRoot } from "../util/path"
import { joinSegments } from "../util/path"

export default (() => {
  const ChatWidget: QuartzComponent = ({ fileData }: QuartzComponentProps) => {
    const baseDir = pathToRoot(fileData.slug!)
    return (
      <>
        <link rel="stylesheet" href={joinSegments(baseDir, "static", "chat.css")} />
        <script src={joinSegments(baseDir, "static", "chat.js")} defer></script>
      </>
    )
  }

  return ChatWidget
}) satisfies QuartzComponentConstructor
