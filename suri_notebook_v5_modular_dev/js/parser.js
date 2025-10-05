
export function parseTextFile(content) {
  const lines = content.split("\n");
  const title = lines[0].replace("#", "").trim();
  const body = lines.slice(1).join("\n");
  return { title, body };
}
