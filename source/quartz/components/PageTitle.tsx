import { pathToRoot, joinSegments } from "../util/path"
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"

const PageTitle: QuartzComponent = ({ fileData, cfg, displayClass }: QuartzComponentProps) => {
  const baseDir = pathToRoot(fileData.slug!)
  const logoPath = joinSegments(baseDir, "static/logo.png")
  return (
    <div class={classNames(displayClass, "page-title")}>
      <a href={baseDir}>
        <img src={logoPath} alt="TRACE Grove" />
      </a>
    </div>
  )
}

PageTitle.css = `
.page-title {
  margin: 0;
}

.page-title a {
  display: block;
  text-decoration: none;
}

.page-title img {
  max-width: 200px;
  height: auto;
  display: block;
  transition: opacity 0.2s ease;
}

.page-title img:hover {
  opacity: 0.8;
}

@media (max-width: 600px) {
  .page-title img {
    max-width: 150px;
  }
}
`

export default (() => PageTitle) satisfies QuartzComponentConstructor
