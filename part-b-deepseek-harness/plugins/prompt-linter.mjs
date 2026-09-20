/**
 * Part B custom plugin #2.
 *
 * This is a deterministic quality gate that an agent can call before starting
 * a task. It intentionally uses no model call, network, or file mutation.
 */

export const name = 'part-b-prompt-linter'
export const inject = ['tools']

function lintPrompt(prompt) {
  const trimmed = prompt.trim()
  const words = trimmed ? trimmed.split(/\s+/).length : 0
  const issues = []

  if (words < 5) issues.push('Prompt is too short; state the task and expected result.')
  if (words > 250) issues.push('Prompt is long; split it into smaller verifiable steps.')
  if (/\b(asap|quickly|somehow|etc\.)\b/i.test(trimmed)) {
    issues.push('Replace vague timing or scope language with a measurable requirement.')
  }
  if (!/\b(test|verify|check|acceptance|expected|must)\b/i.test(trimmed)) {
    issues.push('Add a verification or acceptance criterion.')
  }
  if (!/\b(file|repository|project|code|function|plugin|task)\b/i.test(trimmed)) {
    issues.push('Name the project artifact or software area being changed.')
  }

  return {
    ok: issues.length === 0,
    wordCount: words,
    issues,
  }
}

export function apply(ctx) {
  ctx.tools.register({
    name: 'lint_agent_prompt',
    description:
      'Check an agent task for clarity, scope, and a verifiable outcome before execution.',
    parameters: {
      type: 'object',
      properties: {
        prompt: {
          type: 'string',
          description: 'The proposed task prompt to inspect.',
        },
      },
      required: ['prompt'],
      additionalProperties: false,
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          ok: { type: 'boolean' },
          wordCount: { type: 'integer' },
          issues: {
            type: 'array',
            items: { type: 'string' },
          },
        },
        required: ['ok', 'wordCount', 'issues'],
      },
      render: (_args, value) => [
        {
          type: 'text',
          text: value.ok
            ? `Prompt passed (${value.wordCount} words).`
            : `Prompt needs improvement:\n- ${value.issues.join('\n- ')}`,
        },
      ],
    },
    async execute(args) {
      return lintPrompt(args.prompt)
    },
  })
}

export { lintPrompt }
