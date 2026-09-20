/**
 * Part C custom DeepSeek Harness plugin.
 *
 * The plugin exposes one bounded, model-callable tool. It delegates the
 * numerical benchmark to a local Python process, validates all user inputs,
 * and returns a structured experiment report. No arbitrary command, path, or
 * code is accepted from the model.
 */

import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

export const name = 'part-c-autoresearch-ml'
export const inject = ['tools']

const pluginDirectory = path.dirname(fileURLToPath(import.meta.url))
const partDirectory = path.resolve(pluginDirectory, '..')
const benchmarkScript = path.join(partDirectory, 'benchmark', 'autoresearch.py')
const resultsDirectory = path.join(partDirectory, 'results')

function integerInRange(value, fallback, minimum, maximum) {
  if (value === undefined) return fallback
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new Error(`Value must be an integer between ${minimum} and ${maximum}.`)
  }
  return value
}

function pythonCommand() {
  if (process.env.PYTHON) return process.env.PYTHON
  return process.platform === 'win32' ? 'python' : 'python3'
}

function executeBenchmark({ maxTrials, seed }) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      pythonCommand(),
      [benchmarkScript, '--max-trials', String(maxTrials), '--seed', String(seed), '--output-dir', resultsDirectory, '--json'],
      { cwd: partDirectory, shell: false },
    )

    let stdout = ''
    let stderr = ''
    const timeout = setTimeout(() => {
      child.kill()
      reject(new Error('Autoresearch benchmark exceeded the 30-second safety timeout.'))
    }, 30_000)

    child.stdout.on('data', (chunk) => { stdout += chunk })
    child.stderr.on('data', (chunk) => { stderr += chunk })
    child.on('error', (error) => {
      clearTimeout(timeout)
      reject(new Error(`Could not start Python benchmark: ${error.message}`))
    })
    child.on('close', (code) => {
      clearTimeout(timeout)
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Python benchmark exited with code ${code}.`))
        return
      }
      try {
        resolve(JSON.parse(stdout))
      } catch (error) {
        reject(new Error(`Benchmark returned invalid JSON: ${error.message}`))
      }
    })
  })
}

export function apply(ctx) {
  ctx.tools.register({
    name: 'run_autoresearch_experiment',
    description:
      'Run a bounded ML autoresearch loop, compare validation MSE against a baseline, and return the best reproducible configuration.',
    parameters: {
      type: 'object',
      properties: {
        maxTrials: {
          type: 'integer',
          minimum: 1,
          maximum: 8,
          description: 'Maximum candidate configurations to evaluate. The baseline is always evaluated separately.',
        },
        seed: {
          type: 'integer',
          minimum: 0,
          maximum: 999999,
          description: 'Seed for the deterministic synthetic dataset and split.',
        },
      },
      additionalProperties: false,
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: true,
        properties: {
          runId: { type: 'string' },
          objective: { type: 'string' },
          baseline: { type: 'object' },
          trials: { type: 'array' },
          best: { type: 'object' },
          improvement: { type: 'number' },
          artifactPath: { type: 'string' },
        },
        required: ['runId', 'objective', 'baseline', 'trials', 'best', 'improvement', 'artifactPath'],
      },
      render: (_args, value) => [
        {
          type: 'text',
          text: [
            `Autoresearch run ${value.runId} completed.`,
            `Baseline validation MSE: ${value.baseline.validationMse.toFixed(4)}`,
            `Best validation MSE: ${value.best.validationMse.toFixed(4)}`,
            `Improvement: ${(value.improvement * 100).toFixed(2)}%`,
            `Artifact: ${value.artifactPath}`,
          ].join('\n'),
        },
      ],
    },
    async execute(args = {}) {
      const maxTrials = integerInRange(args.maxTrials, 5, 1, 8)
      const seed = integerInRange(args.seed, 7, 0, 999999)
      return executeBenchmark({ maxTrials, seed })
    },
  })
}
