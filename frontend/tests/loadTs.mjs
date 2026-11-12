import { readFile } from 'node:fs/promises'
import ts from 'typescript'

const modules = new Map()

// Load the production utilities, including their real relative dependencies.
export async function loadTs(url) {
  if (modules.has(url.href)) return modules.get(url.href)
  const source = (await readFile(url, 'utf8')).replaceAll('import.meta.env', '({})')
  let js = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText
  const imports = [...js.matchAll(/from ['"](\.[^'"]+)['"]/g)]
  for (const match of imports) {
    const dependency = await loadTs(new URL(`${match[1]}.ts`, url))
    js = js.replace(match[0], `from '${dependency}'`)
  }
  const compiled = `data:text/javascript;base64,${Buffer.from(js).toString('base64')}`
  modules.set(url.href, compiled)
  return compiled
}
