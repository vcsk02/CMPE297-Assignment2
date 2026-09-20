/**
 * Part B custom plugin #1.
 *
 * It demonstrates the smallest useful DeepSeek Harness plugin shape:
 *   - export a name
 *   - declare the tools service dependency
 *   - register a model-callable tool during apply()
 */

export const name = 'part-b-session-inspector'
export const inject = ['tools']

export function apply(ctx) {
  ctx.tools.register({
    name: 'inspect_harness_environment',
    description:
      'Return safe runtime facts proving that the Part B custom plugin is loaded. '
      + 'Use this for diagnostics; it does not read secrets or modify files.',
    parameters: {
      type: 'object',
      properties: {},
      additionalProperties: false,
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          plugin: { type: 'string' },
          nodeVersion: { type: 'string' },
          platform: { type: 'string' },
          workingDirectory: { type: 'string' },
        },
        required: ['plugin', 'nodeVersion', 'platform', 'workingDirectory'],
      },
      render: (_args, value) => [
        { type: 'text', text: JSON.stringify(value, null, 2) },
      ],
    },
    async execute() {
      return {
        plugin: name,
        nodeVersion: process.version,
        platform: process.platform,
        workingDirectory: process.cwd(),
      }
    },
  })
}
