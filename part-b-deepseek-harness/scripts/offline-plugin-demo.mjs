import { apply as applyInspector } from '../plugins/session-inspector.mjs'
import { apply as applyPromptLinter } from '../plugins/prompt-linter.mjs'

const registrations = []
const fakeContext = {
  tools: {
    register(tool) {
      registrations.push(tool)
      return () => {}
    },
  },
}

applyInspector(fakeContext)
applyPromptLinter(fakeContext)

const inspector = registrations.find(tool => tool.name === 'inspect_harness_environment')
const linter = registrations.find(tool => tool.name === 'lint_agent_prompt')
const inspectorResult = await inspector.execute({}, {})
const weakPrompt = await linter.execute({ prompt: 'Make it better quickly.' }, {})
const strongPrompt = await linter.execute(
  {
    prompt:
      'Add a prompt-linter plugin to this repository, write a deterministic unit test, '
      + 'run the test, and report the expected verification output.',
  },
  {},
)

console.log('Registered custom tools:')
console.log(registrations.map(tool => `- ${tool.name}`).join('\n'))
console.log('\ninspect_harness_environment result:')
console.log(JSON.stringify(inspectorResult, null, 2))
console.log('\nWeak prompt result:')
console.log(JSON.stringify(weakPrompt, null, 2))
console.log('\nStrong prompt result:')
console.log(JSON.stringify(strongPrompt, null, 2))

if (registrations.length !== 2 || weakPrompt.ok || !strongPrompt.ok) {
  throw new Error('Offline Part B plugin demo failed its assertions')
}

console.log('\nOffline Part B plugin demo passed.')
