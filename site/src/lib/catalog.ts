import raw from "../generated/catalog.json";

export interface Skill {
  name: string;
  description: string;
  domain: string;
  type: string;
  language: string;
  keywords: string[];
  compatibility: string;
  entry: string;
  overview_markdown: string;
  when_to_use_markdown: string;
  source_url: string;
}

export interface PhaseOther {
  key: string;
  skill: string;
  note: string;
}

export interface Phase {
  id: string;
  skill: string;
  template_key: string;
  fallback: string | null;
  others: PhaseOther[];
}

export interface Operation {
  id: string;
  effect: string;
  approval_required: boolean;
  dry_run: string;
}

export interface Tool {
  tool_id: string;
  skill: string;
  operations: Operation[];
}

export interface Dependency {
  name: string;
  spec: string;
  kind: string;
}

export interface DocPage {
  source: string;
  slug: string;
  group: string;
  lang: string;
  title: string;
  markdown: string;
  source_url: string;
}

export interface Catalog {
  product_version: string;
  source_sha: string;
  portal_sha: string;
  repo: string;
  hero_markdown: string;
  skill_count: number;
  skills: Skill[];
  phases: Phase[];
  tools: Tool[];
  dependencies: {
    root: Dependency[];
    tools: Dependency[];
    site: Dependency[];
  };
  layers: string[];
  docs: DocPage[];
  allowed_hosts: string[];
}

export const catalog = raw as Catalog;

export function plainText(markdown: string): string {
  return markdown
    .replace(/[*_`[\]]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function domainsInOrder(): string[] {
  const found: string[] = [];
  for (const skill of catalog.skills) {
    if (!found.includes(skill.domain)) found.push(skill.domain);
  }
  return found;
}
