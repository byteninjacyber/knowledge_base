import { QuartzComponent, QuartzComponentConstructor } from "./types"

export default (() => {
  const ChatWidget: QuartzComponent = () => {
    return (
      <>
        <link rel="stylesheet" href="/static/chat.css" />
        <script src="/static/chat.js" defer></script>
      </>
    )
  }

  return ChatWidget
}) satisfies QuartzComponentConstructor
