const SKILL_SYNONYMS: Record<string, string[]> = {
  'javascript': ['js', 'ecmascript', 'es6', 'es2015', 'es2016', 'es2017', 'es2018', 'es2019', 'es2020', 'es2021', 'es2022'],
  'typescript': ['ts', 'typescript'],
  'node.js': ['node', 'nodejs', 'node.js', 'express.js', 'express'],
  'react': ['reactjs', 'react.js', 'react js', 'react'],
  'react native': ['reactnative', 'react-native', 'react_native'],
  'angular': ['angularjs', 'angular.js', 'angular 2', 'angular 4', 'angular 5', 'angular 6', 'angular 7', 'angular 8', 'angular 9', 'angular 10', 'angular 11', 'angular 12', 'angular 13', 'angular 14', 'angular 15', 'angular 16', 'angular 17'],
  'vue': ['vuejs', 'vue.js', 'vue js', 'vue 2', 'vue 3'],
  'python': ['python3', 'python 3', 'python 2'],
  'java': ['java 8', 'java 11', 'java 17', 'java 21', 'j2ee', 'java ee', 'jakarta ee'],
  'c#': ['csharp', 'c sharp', '.net', 'dotnet', 'dot net'],
  'go': ['golang', 'go lang'],
  'rust': ['rustlang', 'rust-lang', 'rust lang'],
  'sql': ['mysql', 'postgresql', 'postgres', 'sql server', 'tsql', 'pl/sql', 'oracle sql', 'sqlite'],
  'aws': ['amazon web services', 'amazon aws', 'aws cloud'],
  'azure': ['microsoft azure', 'azure cloud'],
  'gcp': ['google cloud', 'google cloud platform', 'gcloud'],
  'docker': ['docker', 'containerization', 'containers'],
  'kubernetes': ['k8s', 'kube', 'kubernetes'],
  'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control'],
  'linux': ['unix', 'linux/unix', 'linux administration'],
  'html': ['html5', 'html 5'],
  'css': ['css3', 'css 3', 'css'],
  'sass': ['scss', 'sass'],
  'tailwind': ['tailwind css', 'tailwindcss'],
  'redux': ['redux', 'reduxjs', 'react redux'],
  'graphql': ['graph ql', 'graphql', 'apollo'],
  'rest': ['rest api', 'restful', 'rest apis', 'restful api'],
  'mongodb': ['mongo', 'mongodb', 'mongo db'],
  'redis': ['redis', 'redis cache'],
  'kafka': ['apache kafka', 'kafka'],
  'rabbitmq': ['rabbit mq', 'rabbitmq'],
  'jenkins': ['jenkins', 'ci/cd', 'ci cd'],
  'terraform': ['terraform', 'iac', 'infrastructure as code'],
  'ansible': ['ansible', 'ansible playbook'],
  'agile': ['agile', 'scrum', 'kanban', 'agile/scrum'],
  'machine learning': ['ml', 'machinelearning', 'machine learning'],
  'deep learning': ['dl', 'deeplearning', 'deep learning'],
  'data science': ['datascience', 'data science'],
  'nlp': ['natural language processing', 'nlp'],
  'computer vision': ['cv', 'computervision', 'computer vision'],
  'react testing library': ['rtl', 'react testing library'],
  'jest': ['jest', 'jestjs', 'jest js'],
  'cypress': ['cypress', 'cypress.io'],
  'webpack': ['webpack', 'webpack.js'],
  'vite': ['vitejs', 'vite js', 'vite'],
  'next.js': ['nextjs', 'next.js', 'next js'],
  'nuxt': ['nuxtjs', 'nuxt.js', 'nuxt js'],
  'django': ['django', 'django framework'],
  'flask': ['flask', 'flask framework'],
  'spring': ['spring boot', 'spring framework', 'spring boot', 'spring mvc'],
  'hibernate': ['hibernate', 'hibernate orm', 'jpa'],
  'rails': ['ruby on rails', 'rails', 'ror'],
  'php': ['php', 'php 7', 'php 8'],
  'swift': ['swift', 'swift ios'],
  'kotlin': ['kotlin', 'kotlin android'],
  'flutter': ['flutter', 'flutter framework', 'flutter dart'],
  'dart': ['dart', 'dart lang'],
  'figma': ['figma', 'figma design'],
  'sketch': ['sketch', 'sketch app'],
  'adobe xd': ['xd', 'adobe xd', 'adobexd'],
  'photoshop': ['ps', 'photoshop', 'adobe photoshop'],
  'illustrator': ['ai', 'illustrator', 'adobe illustrator'],
}

export function normalizeSkill(skill: string): string {
  const lower = skill.toLowerCase().trim()
  for (const [canonical, aliases] of Object.entries(SKILL_SYNONYMS)) {
    if (canonical === lower || aliases.includes(lower)) return canonical
  }
  return lower
}

export function expandSkill(skill: string): string[] {
  const normalized = normalizeSkill(skill)
  return [normalized, ...(SKILL_SYNONYMS[normalized] || [])]
}

export function areSkillsSimilar(a: string, b: string): boolean {
  return normalizeSkill(a) === normalizeSkill(b)
}

export function findMatchingSkills(userSkills: string[], jobSkills: string[]): {
  exact: string[]
  similar: string[]
  missing: string[]
  transferable: string[]
} {
  const normalizedUser = userSkills.map(s => ({ original: s, normalized: normalizeSkill(s) }))
  const normalizedJob = jobSkills.map(s => ({ original: s, normalized: normalizeSkill(s) }))

  const exact: string[] = []
  const similar: string[] = []
  const missing: string[] = []
  const transferable: string[] = []

  const userNormSet = new Set(normalizedUser.map(u => u.normalized))

  for (const js of normalizedJob) {
    if (userNormSet.has(js.normalized)) {
      exact.push(js.original)
    } else {
      missing.push(js.original)
    }
  }

  for (const us of normalizedUser) {
    if (!exact.some(e => normalizeSkill(e) === us.normalized)) {
      similar.push(us.original)
    }
  }

  const transferableSkills = ['communication', 'leadership', 'teamwork', 'problem solving', 'analytical', 'critical thinking', 'time management', 'project management', 'presentation', 'writing']
  for (const us of normalizedUser) {
    if (transferableSkills.includes(us.normalized)) {
      transferable.push(us.original)
    }
  }

  return { exact, similar, missing, transferable }
}
