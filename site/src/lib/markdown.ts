import MarkdownIt from "markdown-it";
import markdownItAnchor from "markdown-it-anchor";

const markdown = new MarkdownIt({
  html: false,
  linkify: false,
  typographer: false,
});

markdown.use(markdownItAnchor, { permalink: false });

export function renderMarkdown(source: string): string {
  return markdown
    .render(source)
    .replaceAll("<table>", '<div class="table-wrap"><table>')
    .replaceAll("</table>", "</table></div>");
}
